import { useEffect, useState } from "react";
import MeetingsPage from "../components/MeetingsPage";
import { favoriteAPI, meetingAPI } from "../services/api";

export default function AudioMeetings() {
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
      // הסינון מתבצע בבאקנד לפי access_level=audio
      const [response, favoriteSet] = await Promise.all([
        meetingAPI.getAllMeetings("audio"),
        getFavoriteIdSet(),
      ]);
      const all = response.data || [];
      setMeetings(
        all.map((m) => ({
            id: m.UUID,
            dbId: m.UUID,
            meetingId: String(m.m_number || ""),
            accessLevel: m.accessLevel || "audio",
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
          }))
      );
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load audio meetings.");
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
      title="Audio Meetings"
      accessLevel="audio"
      data={meetings}
      loading={loading}
      error={error}
      onRefresh={loadMeetings}
    />
  );
}
