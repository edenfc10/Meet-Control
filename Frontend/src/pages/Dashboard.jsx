import { useCallback, useEffect, useState } from "react";
import { favoriteAPI, meetingAPI } from "../services/api";
import LiveActivityChart from "../components/LiveActivityChart";
import "../components/MeetingsPage.css";
import "./Dashboard.css";

export default function Dashboard({ language = "en" }) {
  const isHebrew = language === "he";

  const [favorites, setFavorites] = useState([]);
  const [favLoading, setFavLoading] = useState(true);
  const [favError, setFavError] = useState("");

  const [liveStats, setLiveStats] = useState({
    total_active: 0,
    by_type: {
      audio: { meetings: 0, participants: 0 },
      video: { meetings: 0, participants: 0 },
      blast_dial: { meetings: 0, participants: 0 },
      unknown: { meetings: 0, participants: 0 },
    },
  });
  const [liveLoading, setLiveLoading] = useState(true);
  const [liveError, setLiveError] = useState("");
  const [liveWarning, setLiveWarning] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadFavorites = async () => {
    try {
      setFavLoading(true);
      setFavError("");
      const response = await favoriteAPI.getFavoriteMeetings();
      setFavorites(response.data || []);
    } catch (err) {
      setFavError(err.response?.data?.detail || "Failed to load favorites.");
      setFavorites([]);
    } finally {
      setFavLoading(false);
    }
  };

  const handleRemoveFavorite = async (meetingUuid) => {
    try {
      await favoriteAPI.removeFavoriteMeeting(meetingUuid);
      await loadFavorites();
    } catch (err) {
      setFavError(err.response?.data?.detail || "Failed to remove favorite.");
    }
  };

  const loadLiveStats = useCallback(async () => {
    try {
      setLiveLoading(true);
      setLiveError("");
      setLiveWarning("");

      const dbResponse = await meetingAPI.getAllMeetings();
      const meetings = dbResponse.data || [];
      const dbStats = {
        audio: { meetings: 0, participants: 0 },
        video: { meetings: 0, participants: 0 },
        blast_dial: { meetings: 0, participants: 0 },
        unknown: { meetings: 0, participants: 0 },
      };
      meetings.forEach((m) => {
        const mtType = String(m.accessLevel || "").toLowerCase();
        const type = ["audio", "video", "blast_dial"].includes(mtType)
          ? mtType
          : "unknown";
        dbStats[type].meetings += 1;
        dbStats[type].participants += m.participant_count ?? 0;
      });

      let cmsStats = null;
      let cmsWarning = "";
      try {
        const cmsResponse = await meetingAPI.getLiveStatus();
        cmsStats = cmsResponse.data?.by_type || null;
      } catch (cmsErr) {
        if (cmsErr.response?.status === 403) {
          cmsWarning = "CMS access denied - participant counts are from DB fallback";
        } else {
          cmsWarning = "CMS unreachable - participant counts are from DB fallback";
        }
      }

      const stats = {
        audio: {
          meetings: dbStats.audio.meetings,
          participants: cmsStats?.audio?.participants ?? dbStats.audio.participants,
        },
        video: {
          meetings: dbStats.video.meetings,
          participants: cmsStats?.video?.participants ?? dbStats.video.participants,
        },
        blast_dial: {
          meetings: dbStats.blast_dial.meetings,
          participants:
            cmsStats?.blast_dial?.participants ?? dbStats.blast_dial.participants,
        },
        unknown: {
          meetings: dbStats.unknown.meetings,
          participants: cmsStats?.unknown?.participants ?? dbStats.unknown.participants,
        },
      };

      setLiveStats({
        total_active: meetings.length,
        by_type: stats,
      });
      setLiveWarning(cmsWarning || "CMS live participant counts - DB meeting counts");
      setLastUpdated(new Date());
    } catch (err) {
      setLiveError(
        err.response?.data?.detail || "Failed to load live meeting status.",
      );
    } finally {
      setLiveLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFavorites();
  }, []);

  useEffect(() => {
    loadLiveStats();
    const interval = setInterval(loadLiveStats, 30000);
    return () => clearInterval(interval);
  }, [loadLiveStats]);

  const labels = isHebrew
    ? {
        pageTitle: "לוח בקרה",
        liveTitle: "פעילות חיה",
        activeMeetings: "ועידות באוויר",
        audio: "אודיו",
        video: "וידאו",
        blastDial: "הזנקה",
        participantsCount: "משתתפים",
        lastUpdated: "עודכן לאחרונה",
        liveChart: "פעילות חיה לפי סוג ועידה",
        favoriteMeetings: "ועידות מועדפות",
        refresh: "רענן",
        loading: "טוען...",
        saved: "שמורות",
        noFavorites: "אין ועידות מועדפות עדיין.",
        noParticipants: "אין משתתפים",
        noPassword: "ללא סיסמה",
        remove: "הסר",
      }
    : {
        pageTitle: "Dashboard",
        liveTitle: "Live Activity",
        activeMeetings: "Active Meetings",
        audio: "Audio",
        video: "Video",
        blastDial: "Blast Dial",
        participantsCount: "participants",
        lastUpdated: "Last updated",
        liveChart: "Live Activity by Meeting Type",
        favoriteMeetings: "Favorite Meetings",
        refresh: "Refresh",
        loading: "Loading...",
        saved: "saved",
        noFavorites: "No favorites yet.",
        noParticipants: "No participants",
        noPassword: "No password",
        remove: "Remove",
      };

  return (
    <div className="page">
      <h2 className="page-header dashboard-page-title">{labels.pageTitle}</h2>

      <div className="dashboard-split-layout">
        {/* ---- Main area ---- */}
        <div className="dashboard-main-col">
          <div className="card">
            <div className="live-status-header">
              <div className="live-title-wrap">
                <h3 className="card-title" style={{ margin: 0 }}>
                  {labels.liveTitle}
                </h3>
                <span className="live-indicator">
                  <span className="live-dot"></span>
                  LIVE
                </span>
              </div>
              <button className="btn-ghost" onClick={loadLiveStats}>
                {labels.refresh}
              </button>
            </div>

            {liveError && (
              <div className="error-banner" style={{ marginTop: "8px" }}>
                {liveError}
              </div>
            )}
            {liveWarning && (
              <div className="warning-banner" style={{ marginTop: "8px" }}>
                {liveWarning}
              </div>
            )}

            <div className="kpi-grid" style={{ marginTop: "12px" }}>
              <div className="kpi-card kpi-card-total">
                <div className="kpi-label">{labels.activeMeetings}</div>
                <div className={`kpi-value ${liveLoading ? "kpi-loading" : ""}`}>
                  {liveLoading ? "—" : liveStats.total_active}
                </div>
                <div className="kpi-sub">
                  {liveLoading ? labels.loading : labels.liveTitle}
                </div>
              </div>
              <div className="kpi-card kpi-card-audio">
                <div className="kpi-label">{labels.audio}</div>
                <div className={`kpi-value ${liveLoading ? "kpi-loading" : ""}`}>
                  {liveLoading ? "—" : liveStats.by_type.audio.meetings}
                </div>
                <div className="kpi-sub">
                  {liveLoading
                    ? labels.loading
                    : `${liveStats.by_type.audio.participants} ${labels.participantsCount}`}
                </div>
              </div>
              <div className="kpi-card kpi-card-video">
                <div className="kpi-label">{labels.video}</div>
                <div className={`kpi-value ${liveLoading ? "kpi-loading" : ""}`}>
                  {liveLoading ? "—" : liveStats.by_type.video.meetings}
                </div>
                <div className="kpi-sub">
                  {liveLoading
                    ? labels.loading
                    : `${liveStats.by_type.video.participants} ${labels.participantsCount}`}
                </div>
              </div>
              <div className="kpi-card kpi-card-blast">
                <div className="kpi-label">{labels.blastDial}</div>
                <div className={`kpi-value ${liveLoading ? "kpi-loading" : ""}`}>
                  {liveLoading ? "—" : liveStats.by_type.blast_dial.meetings}
                </div>
                <div className="kpi-sub">
                  {liveLoading
                    ? labels.loading
                    : `${liveStats.by_type.blast_dial.participants} ${labels.participantsCount}`}
                </div>
              </div>
            </div>

            {lastUpdated && (
              <div className="live-last-updated">
                {labels.lastUpdated}: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
          </div>

          <div className="card fill">
            <h3 className="card-title">{labels.liveChart}</h3>
            <LiveActivityChart data={liveStats.by_type} language={language} />
          </div>
        </div>

        {/* ---- Favorites side panel ---- */}
        <div className="dashboard-favorites-col">
          <div className="card fill dashboard-favorites-card">
            <div className="dashboard-fav-header">
              <h3 className="card-title" style={{ margin: 0 }}>
                {labels.favoriteMeetings}
              </h3>
              <button className="btn-ghost" onClick={loadFavorites}>
                {labels.refresh}
              </button>
            </div>

            {favLoading && (
              <div className="empty-state" style={{ marginTop: "12px" }}>
                {labels.loading}
              </div>
            )}
            {favError && (
              <div className="error-banner" style={{ marginTop: "8px" }}>
                {favError}
              </div>
            )}

            {!favLoading && !favError && (
              <>
                <div className="favorites-count-badge">
                  {favorites.length} {labels.saved}
                </div>
                {favorites.length === 0 ? (
                  <div className="meetings-empty">{labels.noFavorites}</div>
                ) : (
                  <div className="meetings-list" style={{ marginTop: "8px" }}>
                    {favorites.map((meeting) => (
                      <div
                        key={meeting.meeting_uuid}
                        className={`meeting-item fav-meeting-item fav-type-${(meeting.accessLevel || "unknown").toLowerCase()}`}
                      >
                        <div className="fav-meeting-accent"></div>
                        <div className="fav-meeting-main">
                          <div className="fav-meeting-header">
                            <span className="fav-meeting-id">
                              #{meeting.m_number}
                            </span>
                            <span className="fav-meeting-type">
                              {meeting.accessLevel || "—"}
                            </span>
                          </div>
                          <div className="fav-meeting-details">
                            <span className="fav-meeting-pass">
                              {meeting.password || labels.noPassword}
                            </span>
                            <span className="fav-meeting-participants">
                              {(meeting.participants || []).length > 0
                                ? `${(meeting.participants || []).length} ${labels.participantsCount}`
                                : labels.noParticipants}
                            </span>
                          </div>
                        </div>
                        <button
                          className="meeting-delete-btn fav-meeting-remove"
                          onClick={() =>
                            handleRemoveFavorite(meeting.meeting_uuid)
                          }
                        >
                          {labels.remove}
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
