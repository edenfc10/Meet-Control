import { useEffect, useState } from "react";
import MeetingsPage from "../components/MeetingsPage";
import { favoriteAPI, meetingAPI } from "../services/api";

export default function BlastdialMeetings({ language = "en" }) {
  const isHebrew = language === "he";
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const getFavoriteIdSet = async () => {
    const resp = await favoriteAPI.getFavoriteMeetings();
    const ids = (resp.data || []).map((m) => m.meeting_uuid);
    return new Set(ids);
  };

  const loadMeetings = async () => {
    try {
      setLoading(true);
      setError("");
      // הסינון מתבצע בבאקנד לפי access_level=blast_dial
      const [response, favoriteSet] = await Promise.all([
        meetingAPI.getAllMeetings("blast_dial"),
        getFavoriteIdSet(),
      ]);
      const all = response.data || [];
      setMeetings(
        all.map((m) => ({
          id: m.UUID,
          dbId: m.UUID,
          meetingId: String(m.m_number || ""),
          accessLevel: m.accessLevel || "blast_dial",
          password: m.password || "",
          group: m.groups?.length ? m.groups[0] : "",
          status: "",
          isFavorite: favoriteSet.has(m.UUID),
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
            ? "טעינת ועידות ההזנקה נכשלה."
            : "Failed to load blast-dial meetings."),
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
      title={isHebrew ? "ועידות הזנקה" : "Blast-dial Meetings"}
      accessLevel="blast_dial"
      language={language}
      data={meetings}
      loading={loading}
      error={error}
      onRefresh={loadMeetings}
    />
  );
}
