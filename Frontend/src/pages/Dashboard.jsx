import { useEffect, useMemo, useState } from "react";
import { favoriteAPI, groupAPI, userAPI } from "../services/api";
import "../components/MeetingsPage.css";
import "./Dashboard.css";

export default function Dashboard() {
  const [users, setUsers] = useState([]);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [favorites, setFavorites] = useState([]);
  const [favLoading, setFavLoading] = useState(true);
  const [favError, setFavError] = useState("");

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

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        setError("");
        const [usersResponse, groupsResponse] = await Promise.all([
          userAPI.getAllUsers(),
          groupAPI.listGroups(),
        ]);
        setUsers(usersResponse.data || []);
        setGroups(groupsResponse.data || []);
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

  const totalMeetings = useMemo(
    () => groups.reduce((sum, group) => sum + (group.meetings?.length || 0), 0),
    [groups],
  );

  const totalMembers = useMemo(
    () => groups.reduce((sum, group) => sum + (group.members?.length || 0), 0),
    [groups],
  );

  return (
    <div className="page">
      <h2 className="page-header" style={{ marginBottom: "16px" }}>
        Dashboard
      </h2>

      <div className="dashboard-split-layout">
        {/* ---- Main area ---- */}
        <div className="dashboard-main-col">
          {loading ? (
            <div className="card">
              <div className="empty-state">Loading dashboard data...</div>
            </div>
          ) : null}
          {error ? <div className="error-banner">{error}</div> : null}

          {!loading && !error ? (
            <>
              <div className="kpi-grid">
                <div className="kpi-card">
                  <div className="kpi-label">Users</div>
                  <div className="kpi-value">{users.length}</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-label">Groups</div>
                  <div className="kpi-value">{groups.length}</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-label">Meetings</div>
                  <div className="kpi-value">{totalMeetings}</div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-label">Group Memberships</div>
                  <div className="kpi-value">{totalMembers}</div>
                </div>
              </div>

              <div className="card fill">
                <h3 className="card-title">Group Activity Snapshot</h3>
                <div className="meetings-list">
                  {groups.length === 0 ? (
                    <div className="empty-state">No groups found.</div>
                  ) : (
                    groups.map((group) => (
                      <div key={group.id} className="meeting-row">
                        <div>
                          <div className="meeting-title">{group.name}</div>
                          <div className="meeting-meta">
                            Members: {group.members?.length || 0} &nbsp;·&nbsp;
                            Meetings: {group.meetings?.length || 0}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </>
          ) : null}
        </div>

        {/* ---- Favorites side panel ---- */}
        <div className="dashboard-favorites-col">
          <div className="card fill dashboard-favorites-card">
            <div className="dashboard-fav-header">
              <h3 className="card-title" style={{ margin: 0 }}>
                Favorite Meetings
              </h3>
              <button className="btn-ghost" onClick={loadFavorites}>
                Refresh
              </button>
            </div>

            {favLoading && (
              <div className="empty-state" style={{ marginTop: "12px" }}>
                Loading...
              </div>
            )}
            {favError && (
              <div className="error-banner" style={{ marginTop: "8px" }}>
                {favError}
              </div>
            )}

            {!favLoading && !favError && (
              <>
                <div className="meetings-count" style={{ marginTop: "12px" }}>
                  {favorites.length} saved
                </div>
                {favorites.length === 0 ? (
                  <div className="meetings-empty">No favorites yet.</div>
                ) : (
                  <div className="meetings-list" style={{ marginTop: "8px" }}>
                    {favorites.map((meeting) => (
                      <div key={meeting.meeting_uuid} className="meeting-item">
                        <div className="meeting-info">
                          <span className="meeting-id">
                            #{meeting.m_number}
                          </span>
                          <span className="meeting-group">
                            {(meeting.participants || [])
                              .map((p) => p.username || p.s_id)
                              .join(", ") || "No participants"}
                          </span>
                          <span className="meeting-pass">
                            {meeting.password || "No password"}
                          </span>
                        </div>
                        <div
                          className="meeting-actions"
                          style={{
                            flexDirection: "column",
                            alignItems: "flex-end",
                            gap: "6px",
                          }}
                        >
                          <span className="meeting-badge">
                            {meeting.accessLevel || "—"}
                          </span>
                          <button
                            className="meeting-delete-btn"
                            onClick={() =>
                              handleRemoveFavorite(meeting.meeting_uuid)
                            }
                          >
                            Remove
                          </button>
                        </div>
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
