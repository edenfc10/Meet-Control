import { useEffect, useState } from "react";
import MeetingsPage from "../components/MeetingsPage";
import { favoriteAPI, meetingAPI } from "../services/api";

export default function VideoMeetings({ language = "en" }) {
  const isHebrew = language === "he";
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const getFavoriteIdSet = async () => {
    const resp = await favoriteAPI.getFavoriteMeetings();
    const ids = (resp.data || []).map((m) => String(m.m_number || ""));
    return new Set(ids);
  };

  const loadMeetings = async () => {
    try {
      setLoading(true);
      setError("");
      // הסנכרון מול ה-CMS מתבצע בבאקנד (reconcile) — הסינון לפי access_level=video
      const [response, favoriteSet] = await Promise.all([
        meetingAPI.getAllMeetings("video"),
        getFavoriteIdSet(),
      ]);
      const all = response.data || [];
      setMeetings(
        all.map((m) => ({
          id: m.m_number,
          dbId: m.m_number,
          meetingId: String(m.m_number || ""),
          name: m.name || "",
          accessLevel: m.accessLevel || "video",
          password: m.password || "",
          groups: m.groups || [],
          participantCount: m.participant_count ?? 0,
          status: "",
          isFavorite: favoriteSet.has(String(m.m_number || "")),
          onToggleFavorite: async (meeting) => {
            if (meeting.isFavorite) {
              await favoriteAPI.removeFavoriteMeeting(meeting.dbId);
            } else {
              await favoriteAPI.addFavoriteMeeting(meeting.dbId);
            }
            await loadMeetings();
          },
        })),
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          (isHebrew
            ? "טעינת ועידות הווידאו נכשלה."
            : "Failed to load video meetings."),
      );
      setMeetings([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMeetings();
  }, []);

  return (
    <MeetingsPage
      title={isHebrew ? "ועידות וידאו" : "Video Meetings"}
      accessLevel="video"
      language={language}
      data={meetings}
      loading={loading}
      error={error}
      onRefresh={loadMeetings}
    />
  );
}
