import { useState } from "react";
import { meetingAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./MeetingsPage.css";

function FavoriteIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M12 17.2L6.12 20.67l1.56-6.68L2.5 9.5l6.82-.58L12 2.6l2.68 6.32 6.82.58-5.18 4.49 1.56 6.68z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function EditIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M12 20h9"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M16.5 3.5a2.12 2.12 0 113 3L8 18l-4 1 1-4 11.5-11.5z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function DeleteIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        d="M3 6h18"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
      <path
        d="M8 6V4h8v2m-1 0v13a2 2 0 01-2 2h-2a2 2 0 01-2-2V6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M10 11v6M14 11v6"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

// קומפוננטה גנרית להצגת דף ישיבות (Audio / Video / Blast-dial)
export default function MeetingsPage({
  title,
  accessLevel,
  language = "en",
  data = [],
  loading,
  error,
  onRefresh,
}) {
  const isHebrew = language === "he";
  const { currentUser } = useAuth();
  const userRole = currentUser?.role?.toLowerCase() || "";
  const canCreateMeeting = userRole === "super_admin";
  const isAdmin = userRole === "admin" || userRole === "super_admin";
  const canEditPassword = isAdmin || userRole === "agent";

  const [showCreate, setShowCreate] = useState(false);
  const [mNumber, setMNumber] = useState("");
  const [password, setPassword] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState("");
  const [meetingToDelete, setMeetingToDelete] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const [editId, setEditId] = useState(null); // UUID של הפגישה שנערכת
  const [editPassword, setEditPassword] = useState("");
  const [editError, setEditError] = useState("");
  const [saving, setSaving] = useState(false);
  const [favoriteBusyId, setFavoriteBusyId] = useState(null);

  const text = {
    cancel: isHebrew ? "ביטול" : "Cancel",
    createMeeting: isHebrew ? "צור ועידה" : "Create Meeting",
    createMeetingTypeTitle: isHebrew
      ? `יצירת ${title}`
      : `Create ${title.replace(" Meetings", "")} Meeting`,
    meetingNumberPlaceholder: isHebrew
      ? "מספר ועידה (למשל 891234)"
      : "Meeting number (e.g. 891234)",
    passwordOptionalPlaceholder: isHebrew
      ? "סיסמה (אופציונלי)"
      : "Password (optional)",
    creating: isHebrew ? "יוצר..." : "Creating...",
    create: isHebrew ? "צור" : "Create",
    createError: isHebrew
      ? "יצירת הוועידה נכשלה."
      : "Failed to create meeting.",
    updatePasswordError: isHebrew
      ? "עדכון הסיסמה נכשל."
      : "Failed to update password.",
    deleteConfirm: isHebrew
      ? "למחוק את הוועידה הזאת? אי אפשר לבטל את הפעולה."
      : "Delete meeting {meetingLabel}? This action cannot be undone.",
    deleteError: isHebrew
      ? "מחיקת הוועידה נכשלה."
      : "Failed to delete meeting.",
    loadingMeetings: isHebrew ? "טוען ועידות..." : "Loading meetings...",
    searchPlaceholder: isHebrew
      ? "חיפוש לפי מספר ועידה או קבוצה..."
      : "Search by meeting number or group...",
    refresh: isHebrew ? "רענון" : "Refresh",
    of: isHebrew ? "מתוך" : "of",
    noMeetings: isHebrew ? "לא נמצאו ועידות." : "No meetings found.",
    noMeetingsMatch: isHebrew
      ? "לא נמצאו ועידות שמתאימות לחיפוש."
      : "No meetings match your search.",
    meeting: isHebrew ? "ועידה" : "Meeting",
    group: isHebrew ? "קבוצה" : "Group",
    noGroup: isHebrew ? "ללא קבוצה" : "No group",
    password: isHebrew ? "סיסמה" : "Password",
    noPassword: isHebrew ? "אין סיסמה" : "No password",
    saving: isHebrew ? "שומר..." : "Saving...",
    removeFavorite: isHebrew ? "הסר ממועדפים" : "Remove Favorite",
    addFavorite: isHebrew ? "הוסף למועדפים" : "Add Favorite",
    editPassword: isHebrew ? "עריכת סיסמה" : "Edit Password",
    deleting: isHebrew ? "מוחק..." : "Deleting...",
    delete: isHebrew ? "מחק" : "Delete",
    deleteModalTitle: isHebrew ? "מחיקת ועידה" : "Delete Meeting",
    deleteModalMessage: isHebrew
      ? "האם למחוק את הוועידה"
      : "Are you sure you want to delete meeting",
    deleteMeeting: isHebrew ? "מחק ועידה" : "Delete Meeting",
    newPasswordPlaceholder: isHebrew ? "סיסמה חדשה" : "New password",
    save: isHebrew ? "שמור" : "Save",
  };

  const accessLevelLabel = (value) => {
    const level = (value || "").toString().toLowerCase();
    if (!isHebrew) {
      return level || "—";
    }
    if (level === "audio") return "אודיו";
    if (level === "video") return "וידאו";
    if (level === "blast_dial") return "הזנקה";
    return level || "—";
  };

  const accessLevelIcon = (value) => {
    const level = (value || "").toString().toLowerCase();
    if (level === "video") return "📹";
    if (level === "audio") return "🎧";
    if (level === "blast_dial") return "🚀";
    return "";
  };

  // חיפוש
  const [search, setSearch] = useState("");
  const filtered = data.filter(
    (m) =>
      (m.meetingId || "").toLowerCase().includes(search.toLowerCase()) ||
      (m.group || "").toLowerCase().includes(search.toLowerCase()),
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
      setCreateError(err.response?.data?.detail || text.createError);
    } finally {
      setCreating(false);
    }
  };

  const handleEditSave = async (meeting) => {
    setSaving(true);
    setEditError("");
    try {
      await meetingAPI.updateMeetingPassword(
        meeting.dbId,
        editPassword.trim() || null,
      );
      setEditId(null);
      setEditPassword("");
      if (onRefresh) onRefresh();
    } catch (err) {
      setEditError(err.response?.data?.detail || text.updatePasswordError);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (meeting) => {
    setMeetingToDelete(meeting);
    setShowDeleteConfirm(true);
  };

  const closeDeleteConfirm = () => {
    setMeetingToDelete(null);
    setShowDeleteConfirm(false);
  };

  const confirmDeleteMeeting = async () => {
    if (!meetingToDelete) return;

    setDeletingId(meetingToDelete.dbId);
    setDeleteError("");
    try {
      await meetingAPI.deleteMeeting(meetingToDelete.dbId);
      if (editId === meetingToDelete.dbId) {
        setEditId(null);
        setEditPassword("");
      }
      closeDeleteConfirm();
      if (onRefresh) onRefresh();
    } catch (err) {
      setDeleteError(err.response?.data?.detail || text.deleteError);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className={`meetings-page meetings-page--${accessLevel}`}>
      <div className="meetings-header">
        <h2 className="meetings-title">{title}</h2>
        {canCreateMeeting ? (
          <button
            className="meetings-create-btn"
            onClick={() => setShowCreate(!showCreate)}
          >
            {showCreate ? text.cancel : `+ ${text.createMeeting}`}
          </button>
        ) : null}
      </div>

      {canCreateMeeting && showCreate && (
        <div className="meetings-create-card">
          <h3>{text.createMeetingTypeTitle}</h3>
          <div className="meetings-create-row">
            <input
              type="text"
              placeholder={text.meetingNumberPlaceholder}
              value={mNumber}
              onChange={(e) => setMNumber(e.target.value)}
              className="meetings-create-input"
            />
            <input
              type="text"
              placeholder={text.passwordOptionalPlaceholder}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="meetings-create-input"
            />
            <button
              className="meetings-create-submit"
              onClick={handleCreate}
              disabled={creating || !mNumber.trim()}
            >
              {creating ? text.creating : text.create}
            </button>
          </div>
          {createError && <div className="meetings-error">{createError}</div>}
        </div>
      )}

      {loading && <div className="meetings-status">{text.loadingMeetings}</div>}
      {error && <div className="meetings-status meetings-error">{error}</div>}

      {!loading && !error && (
        <div className="meetings-card">
          <div className="meetings-search-row">
            <input
              className="meetings-search-input"
              type="text"
              placeholder={text.searchPlaceholder}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <button
              className="btn-ghost meetings-refresh-btn"
              onClick={onRefresh}
            >
              {text.refresh}
            </button>
          </div>
          <div className="meetings-count">
            {title} ({filtered.length}
            {filtered.length !== data.length
              ? ` ${text.of} ${data.length}`
              : ""}
            )
          </div>

          {filtered.length === 0 ? (
            <div className="meetings-empty">
              {data.length === 0 ? text.noMeetings : text.noMeetingsMatch}
            </div>
          ) : (
            <div className="meetings-list">
              {filtered.map((meeting) => (
                <div key={meeting.id} className="meeting-item">
                  <div className="meeting-info">
                    <span className="meeting-id">
                      {text.meeting} #
                      {meeting.meetingId || meeting.dbId?.slice(0, 8)}
                    </span>
                    <span className="meeting-uuid">
                      UUID: {meeting.dbId || "—"}
                    </span>
                    <span className="meeting-group">
                      {text.group}:{" "}
                      {meeting.group
                        ? String(meeting.group).slice(0, 8) + "..."
                        : text.noGroup}
                    </span>
                    <span className="meeting-pass">
                      {text.password}: {meeting.password || text.noPassword}
                    </span>
                  </div>
                  <div className="meeting-actions">
                    {typeof meeting.isFavorite === "boolean" && (
                      <button
                        className={
                          meeting.isFavorite
                            ? "meeting-favorite-btn active"
                            : "meeting-favorite-btn"
                        }
                        onClick={() => handleFavoriteToggle(meeting)}
                        disabled={favoriteBusyId === meeting.dbId}
                      >
                        <span className="action-btn-content">
                          <span className="action-btn-icon">
                            <FavoriteIcon />
                          </span>
                          <span>
                            {favoriteBusyId === meeting.dbId
                              ? text.saving
                              : meeting.isFavorite
                                ? text.removeFavorite
                                : text.addFavorite}
                          </span>
                        </span>
                      </button>
                    )}
                    {canEditPassword && (
                      <>
                        <button
                          className="meeting-edit-btn"
                          onClick={() => {
                            setEditId(meeting.dbId);
                            setEditPassword(meeting.password || "");
                            setEditError("");
                          }}
                        >
                          <span className="action-btn-content">
                            <span className="action-btn-icon">
                              <EditIcon />
                            </span>
                            <span>{text.editPassword}</span>
                          </span>
                        </button>
                        {isAdmin && (
                          <button
                            className="meeting-delete-btn"
                            onClick={() => handleDelete(meeting)}
                            disabled={deletingId === meeting.dbId}
                          >
                            <span className="action-btn-content">
                              <span className="action-btn-icon">
                                <DeleteIcon />
                              </span>
                              <span>
                                {deletingId === meeting.dbId
                                  ? text.deleting
                                  : text.delete}
                              </span>
                            </span>
                          </button>
                        )}
                      </>
                    )}
                    <span
                      className={`meeting-badge meeting-badge--${(meeting.accessLevel || "").toString().toLowerCase()}`}
                    >
                      <span>{accessLevelLabel(meeting.accessLevel)}</span>
                      {accessLevelIcon(meeting.accessLevel) ? (
                        <span className="meeting-badge-icon" aria-hidden="true">
                          {accessLevelIcon(meeting.accessLevel)}
                        </span>
                      ) : null}
                    </span>
                  </div>
                  {canEditPassword && editId === meeting.dbId && (
                    <div className="meeting-edit-row">
                      <input
                        type="text"
                        placeholder={text.newPasswordPlaceholder}
                        value={editPassword}
                        onChange={(e) => setEditPassword(e.target.value)}
                        className="meetings-create-input"
                      />
                      <button
                        className="meetings-create-submit"
                        onClick={() => handleEditSave(meeting)}
                        disabled={saving}
                      >
                        {saving ? text.saving : text.save}
                      </button>
                      <button
                        className="meeting-cancel-btn"
                        onClick={() => {
                          setEditId(null);
                          setEditPassword("");
                        }}
                      >
                        {text.cancel}
                      </button>
                      {editError && (
                        <span className="meetings-error">{editError}</span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          {deleteError && (
            <div className="meetings-error meetings-inline-error">
              {deleteError}
            </div>
          )}
        </div>
      )}

      {showDeleteConfirm && meetingToDelete ? (
        <div className="modal-overlay" onClick={closeDeleteConfirm}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">{text.deleteModalTitle}</h3>
            <p
              style={{
                marginBottom: "20px",
                color: "#d32f2f",
                fontWeight: "500",
              }}
            >
              {text.deleteModalMessage} "
              {meetingToDelete.meetingId || meetingToDelete.dbId?.slice(0, 8)}"
              ?
            </p>

            <div className="modal-actions">
              <button
                className="btn-secondary"
                type="button"
                onClick={closeDeleteConfirm}
                disabled={deletingId === meetingToDelete.dbId}
              >
                {text.cancel}
              </button>
              <button
                className="btn-danger"
                type="button"
                onClick={confirmDeleteMeeting}
                disabled={deletingId === meetingToDelete.dbId}
              >
                {deletingId === meetingToDelete.dbId
                  ? text.deleting
                  : text.deleteMeeting}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
