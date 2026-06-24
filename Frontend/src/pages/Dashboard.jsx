import { useCallback, useEffect, useState } from "react";
import { favoriteAPI, groupAPI, meetingAPI } from "../services/api";
import "../components/MeetingsPage.css";
import "./Dashboard.css";

export default function Dashboard({ language = "en" }) {
  const isHebrew = language === "he";

  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [meetingCountByGroup, setMeetingCountByGroup] = useState({});

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
      const response = await meetingAPI.getLiveStatus();
      setLiveStats(
        response.data || {
          total_active: 0,
          by_type: {
            audio: { meetings: 0, participants: 0 },
            video: { meetings: 0, participants: 0 },
            blast_dial: { meetings: 0, participants: 0 },
            unknown: { meetings: 0, participants: 0 },
          },
        },
      );
      setLiveWarning(response.data?.warning || "");
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
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError("");
        const [groupsResp, meetingsResp] = await Promise.all([
          groupAPI.listGroups(),
          meetingAPI.getAllMeetings(),
        ]);
        const groupsList = groupsResp.data || [];
        setGroups(groupsList);
        const countMap = {};
        (meetingsResp.data || []).forEach((m) => {
          (m.groups || []).forEach((gUUID) => {
            const key = String(gUUID).toLowerCase();
            countMap[key] = (countMap[key] || 0) + 1;
          });
        });
        setMeetingCountByGroup(countMap);
      } catch (err) {
        setError(
          err.response?.data?.detail || "Failed to load dashboard data.",
        );
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
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
        loadingDashboard: "טוען נתוני לוח בקרה...",
        liveTitle: "פעילות חיה",
        activeMeetings: "ועידות באוויר",
        audio: "אודיו",
        video: "וידאו",
        blastDial: "חיוג המוני",
        meetingsCount: "ועידות",
        participantsCount: "משתתפים",
        lastUpdated: "עודכן לאחרונה",
        snapshot: "תמונת מצב פעילות מדורים",
        noGroups: "לא נמצאו קבוצות.",
        members: "חברים",
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
        loadingDashboard: "Loading dashboard data...",
        liveTitle: "Live Activity",
        activeMeetings: "Active Meetings",
        audio: "Audio",
        video: "Video",
        blastDial: "Blast Dial",
        meetingsCount: "meetings",
        participantsCount: "participants",
        lastUpdated: "Last updated",
        snapshot: "Group Activity Snapshot",
        noGroups: "No groups found.",
        members: "Members",
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
                  {liveLoading ? "—" : liveStats.by_type.audio.participants}
                </div>
                <div className="kpi-sub">
                  {liveLoading
                    ? labels.loading
                    : `${liveStats.by_type.audio.meetings} ${labels.meetingsCount}`}
                </div>
              </div>
              <div className="kpi-card kpi-card-video">
                <div className="kpi-label">{labels.video}</div>
                <div className={`kpi-value ${liveLoading ? "kpi-loading" : ""}`}>
                  {liveLoading ? "—" : liveStats.by_type.video.participants}
                </div>
                <div className="kpi-sub">
                  {liveLoading
                    ? labels.loading
                    : `${liveStats.by_type.video.meetings} ${labels.meetingsCount}`}
                </div>
              </div>
              <div className="kpi-card kpi-card-blast">
                <div className="kpi-label">{labels.blastDial}</div>
                <div className={`kpi-value ${liveLoading ? "kpi-loading" : ""}`}>
                  {liveLoading ? "—" : liveStats.by_type.blast_dial.participants}
                </div>
                <div className="kpi-sub">
                  {liveLoading
                    ? labels.loading
                    : `${liveStats.by_type.blast_dial.meetings} ${labels.meetingsCount}`}
                </div>
              </div>
            </div>

            {lastUpdated && (
              <div className="live-last-updated">
                {labels.lastUpdated}: {lastUpdated.toLocaleTimeString()}
              </div>
            )}
          </div>

          {loading ? (
            <div className="card">
              <div className="empty-state">{labels.loadingDashboard}</div>
            </div>
          ) : null}
          {error ? <div className="error-banner">{error}</div> : null}

          {!loading && !error ? (
            <div className="card fill">
              <h3 className="card-title">{labels.snapshot}</h3>
              <div className="meetings-list">
                {groups.length === 0 ? (
                  <div className="empty-state">{labels.noGroups}</div>
                ) : (
                  groups.map((group) => (
                    <div
                      key={group.UUID || group.id || group.name}
                      className="meeting-row group-snapshot-row"
                    >
                      <div className="group-snapshot-left">
                        <div className="group-snapshot-avatar">
                          {group.name
                            ? group.name.charAt(0).toUpperCase()
                            : "G"}
                        </div>
                        <div className="group-snapshot-info">
                          <div className="meeting-title">{group.name}</div>
                          <div className="group-snapshot-meta">
                            <span className="group-meta-chip">
                              {labels.members}: {group.members?.length || 0}
                            </span>
                            <span className="group-meta-chip">
                              {labels.meetingsCount}: {meetingCountByGroup[String(group.UUID).toLowerCase()] || 0}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="group-snapshot-stat">
                        <div className="group-stat-value">
                          {meetingCountByGroup[String(group.UUID).toLowerCase()] || 0}
                        </div>
                        <div className="group-stat-label">
                          {labels.meetingsCount}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          ) : null}
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
