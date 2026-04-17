import { useState } from "react";
import { meetingAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./MeetingsPage.css";

// קומפוננטה גנרית להצגת דף ישיבות (Audio / Video / Blast-dial)
export default function MeetingsPage({ title, accessLevel, data = [], loading, error, onRefresh }) {
  const { currentUser } = useAuth();
  const userRole = currentUser?.role?.toLowerCase() || "";
  const isAdmin = userRole === "admin" || userRole === "super_admin";

  const [showCreate, setShowCreate] = useState(false);
  const [mNumber, setMNumber] = useState("");
  const [password, setPassword] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState("");

  const [editId, setEditId] = useState(null); // UUID של הפגישה שנערכת
  const [editPassword, setEditPassword] = useState("");
  const [editError, setEditError] = useState("");
  const [saving, setSaving] = useState(false);
  const [favoriteBusyId, setFavoriteBusyId] = useState(null);

  // חיפוש
  const [search, setSearch] = useState("");
  const filtered = data.filter((m) =>
    (m.meetingId || "").toLowerCase().includes(search.toLowerCase()) ||
    (m.group || "").toLowerCase().includes(search.toLowerCase())
  );

  const handleFavoriteToggle = async (meeting) => {
    if (!meeting?.onToggleFavorite) return;
    setFavoriteBusyId(meeting.dbId);
    try {
      await meeting.onToggleFavorite(meeting);
    } finally {
      setFavoriteBusyId(null);
    }
  };

  const handleCreate = async () => {
    if (!mNumber.trim()) return;
    setCreating(true);
    setCreateError("");
    try {
      await meetingAPI.createMeeting({
        m_number: mNumber.trim(),
        accessLevel,
        ...(password.trim() ? { password: password.trim() } : {}),
      });
      setMNumber("");
      setPassword("");
      setShowCreate(false);
      if (onRefresh) onRefresh();
    } catch (err) {
      setCreateError(err.response?.data?.detail || "Failed to create meeting.");
    } finally {
      setCreating(false);
    }
  };

  const handleEditSave = async (meeting) => {
    setSaving(true);
    setEditError("");
    try {
      await meetingAPI.updateMeeting(meeting.dbId, { password: editPassword.trim() || null });
      setEditId(null);
      setEditPassword("");
      if (onRefresh) onRefresh();
    } catch (err) {
      setEditError(err.response?.data?.detail || "Failed to update password.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (meeting) => {
    const meetingLabel = meeting.meetingId || meeting.dbId;
    const confirmed = window.confirm(
      `Delete meeting ${meetingLabel}? This action cannot be undone.`
    );
    if (!confirmed) return;

    setDeletingId(meeting.dbId);
    setDeleteError("");
    try {
      await meetingAPI.deleteMeeting(meeting.dbId);
      if (editId === meeting.dbId) {
        setEditId(null);
        setEditPassword("");
      }
      if (onRefresh) onRefresh();
    } catch (err) {
      setDeleteError(err.response?.data?.detail || "Failed to delete meeting.");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="meetings-page">
      <div className="meetings-header">
        <h2 className="meetings-title">{title}</h2>
        <button className="meetings-create-btn" onClick={() => setShowCreate(!showCreate)}>
          {showCreate ? "Cancel" : "+ Create Meeting"}
        </button>
      </div>

      {showCreate && (
        <div className="meetings-create-card">
          <h3>Create {title.replace(" Meetings", "")} Meeting</h3>
          <div className="meetings-create-row">
            <input
              type="text"
              placeholder="Meeting number (e.g. 891234)"
              value={mNumber}
              onChange={(e) => setMNumber(e.target.value)}
              className="meetings-create-input"
            />
            <input
              type="text"
              placeholder="Password (optional)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="meetings-create-input"
            />
            <button
              className="meetings-create-submit"
              onClick={handleCreate}
              disabled={creating || !mNumber.trim()}
            >
              {creating ? "Creating..." : "Create"}
            </button>
          </div>
          {createError && <div className="meetings-error">{createError}</div>}
        </div>
      )}

      {loading && <div className="meetings-status">Loading meetings...</div>}
      {error && <div className="meetings-status meetings-error">{error}</div>}

      {!loading && !error && (
        <div className="meetings-card">
          <div className="meetings-search-row">
            <input
              className="meetings-search-input"
              type="text"
              placeholder="Search by meeting number or group..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <button className="btn-ghost meetings-refresh-btn" onClick={onRefresh}>Refresh</button>
          </div>
          <div className="meetings-count">
            {title} ({filtered.length}{filtered.length !== data.length ? ` of ${data.length}` : ""})
          </div>

          {filtered.length === 0 ? (
            <div className="meetings-empty">{data.length === 0 ? "No meetings found." : "No meetings match your search."}</div>
          ) : (
            <div className="meetings-list">
              {filtered.map((meeting) => (
                <div key={meeting.id} className="meeting-item">
                  <div className="meeting-info">
                    <span className="meeting-id">
                      Meeting #{meeting.meetingId || meeting.dbId?.slice(0, 8)}
                    </span>
                    <span className="meeting-uuid">
                      UUID: {meeting.dbId || "—"}
                    </span>
                    <span className="meeting-group">
                      Group: {meeting.group ? String(meeting.group).slice(0, 8) + "..." : "No group"}
                    </span>
                    <span className="meeting-pass">
                      Password: {meeting.password || "No password"}
                    </span>
                  </div>
                  <div className="meeting-actions">
                    {typeof meeting.isFavorite === "boolean" && (
                      <button
                        className={meeting.isFavorite ? "meeting-favorite-btn active" : "meeting-favorite-btn"}
                        onClick={() => handleFavoriteToggle(meeting)}
                        disabled={favoriteBusyId === meeting.dbId}
                      >
                        {favoriteBusyId === meeting.dbId
                          ? "Saving..."
                          : meeting.isFavorite
                            ? "Remove Favorite"
                            : "Add Favorite"}
                      </button>
                    )}
                    <span className="meeting-badge">
                      {meeting.accessLevel || "—"}
                    </span>
                    {isAdmin && (
                      <>
                        <button
                          className="meeting-edit-btn"
                          onClick={() => {
                            setEditId(meeting.dbId);
                            setEditPassword(meeting.password || "");
                            setEditError("");
                          }}
                        >
                          Edit Password
                        </button>
                        <button
                          className="meeting-delete-btn"
                          onClick={() => handleDelete(meeting)}
                          disabled={deletingId === meeting.dbId}
                        >
                          {deletingId === meeting.dbId ? "Deleting..." : "Delete"}
                        </button>
                      </>
                    )}
                  </div>
                  {isAdmin && editId === meeting.dbId && (
                    <div className="meeting-edit-row">
                      <input
                        type="text"
                        placeholder="New password"
                        value={editPassword}
                        onChange={(e) => setEditPassword(e.target.value)}
                        className="meetings-create-input"
                      />
                      <button
                        className="meetings-create-submit"
                        onClick={() => handleEditSave(meeting)}
                        disabled={saving}
                      >
                        {saving ? "Saving..." : "Save"}
                      </button>
                      <button
                        className="meeting-cancel-btn"
                        onClick={() => { setEditId(null); setEditPassword(""); }}
                      >
                        Cancel
                      </button>
                      {editError && <span className="meetings-error">{editError}</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          {deleteError && <div className="meetings-error meetings-inline-error">{deleteError}</div>}
        </div>
      )}
    </div>
  );
}
