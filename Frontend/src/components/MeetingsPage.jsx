import { useState, useEffect } from "react";
import { meetingAPI, groupAPI } from "../services/api";
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
  const canCreateMeeting = userRole === "super_admin" && accessLevel !== "audio";
  const isAdmin = userRole === "admin" || userRole === "super_admin";
  const canEditPassword = isAdmin;
  const canEditName = isAdmin && accessLevel !== "audio";

  const [showCreate, setShowCreate] = useState(false);
  const [mNumber, setMNumber] = useState("");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [deletingId, setDeletingId] = useState(null);
  const [deleteError, setDeleteError] = useState("");
  const [meetingToDelete, setMeetingToDelete] = useState(null);
  const [assignGroupModal, setAssignGroupModal] = useState(null);
  const [assignGroupId, setAssignGroupId] = useState("");
  const [assignLoading, setAssignLoading] = useState(false);
  const [assignError, setAssignError] = useState("");
  const [confirmRemoveAssign, setConfirmRemoveAssign] = useState(false);

  const [toast, setToast] = useState(null);
  const showToast = (message, type = "success") => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const [sortField, setSortField] = useState("number");
  const [sortDir, setSortDir] = useState("asc");
  const [page, setPage] = useState(1);
  const PAGE_SIZE = 10;
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const [participantsModal, setParticipantsModal] = useState(null);
  const [participantsLoading, setParticipantsLoading] = useState(false);
  const [participantsError, setParticipantsError] = useState("");
  const [participants, setParticipants] = useState([]);

  const [activeTab, setActiveTab] = useState("authorized");
  const [liveLoading, setLiveLoading] = useState(false);
  const [liveError, setLiveError] = useState("");
  const [liveParticipants, setLiveParticipants] = useState([]);
  const [liveCallId, setLiveCallId] = useState(null);
  const [muteLoadingId, setMuteLoadingId] = useState(null);
  const [kickLoadingId, setKickLoadingId] = useState(null);

  const handleLoadLive = async (meeting) => {
    setLiveParticipants([]);
    setLiveCallId(null);
    setLiveError("");
    setLiveLoading(true);
    try {
      const resp = await meetingAPI.getLiveParticipants(meeting.dbId);
      setLiveParticipants(resp.data.participants || []);
      setLiveCallId(resp.data.call_id || null);
    } catch {
      setLiveError(isHebrew ? "טעינת משתתפים חיים נכשלה." : "Failed to load live participants.");
    } finally {
      setLiveLoading(false);
    }
  };

  const handleTabChange = (tab, meeting) => {
    setActiveTab(tab);
    if (tab === "live" && liveParticipants.length === 0 && !liveLoading) {
      handleLoadLive(meeting);
    }
  };

  const handleMute = async (legId, currentMute) => {
    if (!participantsModal) return;
    setMuteLoadingId(legId);
    try {
      await meetingAPI.muteParticipant(participantsModal.dbId, liveCallId, legId, !currentMute);
      setLiveParticipants((prev) =>
        prev.map((p) =>
          (p.legId || p["@id"]) === legId ? { ...p, mute: (!currentMute).toString() } : p
        )
      );
    } catch {
      setLiveError(isHebrew ? "פעולת השתקה נכשלה." : "Mute action failed.");
    } finally {
      setMuteLoadingId(null);
    }
  };

  const handleKick = async (legId) => {
    if (!participantsModal) return;
    setKickLoadingId(legId);
    try {
      await meetingAPI.kickParticipant(participantsModal.dbId, liveCallId, legId);
      setLiveParticipants((prev) =>
        prev.filter((p) => (p.legId || p["@id"]) !== legId)
      );
    } catch {
      setLiveError(isHebrew ? "פעולת הסרה נכשלה." : "Kick action failed.");
    } finally {
      setKickLoadingId(null);
    }
  };

  const [editId, setEditId] = useState(null); // UUID של הפגישה שנערכת
  const [editPassword, setEditPassword] = useState("");
  const [editName, setEditName] = useState("");
  const [editNameId, setEditNameId] = useState(null);
  const [editNameError, setEditNameError] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [editError, setEditError] = useState("");
  const [saving, setSaving] = useState(false);
  const [favoriteBusyId, setFavoriteBusyId] = useState(null);

  const handleViewParticipants = async (meeting) => {
    setParticipantsModal(meeting);
    setActiveTab("authorized");
    setParticipants([]);
    setParticipantsError("");
    setLiveParticipants([]);
    setLiveCallId(null);
    setLiveError("");
    setParticipantsLoading(true);
    try {
      const resp = await meetingAPI.getParticipants(meeting.dbId);
      setParticipants(resp.data.participants || []);
    } catch {
      setParticipantsError(isHebrew ? "טעינת משתתפים נכשלה." : "Failed to load participants.");
    } finally {
      setParticipantsLoading(false);
    }
  };

  const text = {
    cancel: isHebrew ? "ביטול" : "Cancel",
    createMeeting: isHebrew ? "צור ועידה" : "Create Meeting",
    createMeetingTypeTitle: isHebrew ? `יצירת ${title}` : `Create ${title.replace(" Meetings", "")} Meeting`,
    meetingNumberPlaceholder: isHebrew ? "מספר ועידה (למשל 891234)" : "Meeting number (e.g. 891234)",
    meetingNamePlaceholder: isHebrew ? "שם ועידה" : "Meeting name",
    passwordOptionalPlaceholder: isHebrew ? "סיסמה (אופציונלי)" : "Password (optional)",
    creating: isHebrew ? "יוצר..." : "Creating...",
    create: isHebrew ? "צור" : "Create",
    createError: isHebrew ? "יצירת הוועידה נכשלה." : "Failed to create meeting.",
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
    searchByAll: isHebrew ? "הכל" : "All",
    searchByNameOrNumber: isHebrew ? "שם או מספר" : "Name or Number",
    searchByGroup: isHebrew ? "שם מדור" : "Group Name",
    searchByNoGroup: isHebrew ? "ללא מדור" : "No group",
    searchPlaceholderNumber: isHebrew ? "הקלד מספר ועידה..." : "Enter meeting number...",
    searchPlaceholderName: isHebrew ? "הקלד שם ועידה..." : "Enter meeting name...",
    searchPlaceholderNameOrNumber: isHebrew ? "הקלד שם או מספר ועידה..." : "Enter meeting name or number...",
    searchPlaceholderGroup: isHebrew ? "הקלד שם מדור..." : "Enter group name...",
    refresh: isHebrew ? "רענון" : "Refresh",
    of: isHebrew ? "מתוך" : "of",
    noMeetings: isHebrew ? "לא נמצאו ועידות." : "No meetings found.",
    noMeetingsMatch: isHebrew
      ? "לא נמצאו ועידות שמתאימות לחיפוש."
      : "No meetings match your search.",
    meeting: isHebrew ? "ועידה" : "Meeting",
    meetingNumber: isHebrew ? "מספר ועידה" : "Meeting Number",
    group: isHebrew ? "מדור" : "Group",
    noGroup: isHebrew ? "ללא מדור" : "No group",
    participants: isHebrew ? "משתתפים" : "Participants",
    password: isHebrew ? "סיסמה" : "Password",
    noPassword: isHebrew ? "אין סיסמה" : "No password",
    saving: isHebrew ? "שומר..." : "Saving...",
    removeFavorite: isHebrew ? "הסר ממועדפים" : "Remove Favorite",
    addFavorite: isHebrew ? "הוסף למועדפים" : "Add Favorite",
    editName: isHebrew ? "עריכת שם" : "Edit Name",
    editPassword: isHebrew ? "עריכת סיסמה" : "Edit Password",
    deleting: isHebrew ? "מוחק..." : "Deleting...",
    delete: isHebrew ? "מחק" : "Delete",
    deleteModalTitle: isHebrew ? "מחיקת ועידה" : "Delete Meeting",
    deleteModalMessage: isHebrew
      ? "האם למחוק את הוועידה"
      : "Are you sure you want to delete meeting",
    deleteMeeting: isHebrew ? "מחק ועידה" : "Delete Meeting",
    newPasswordPlaceholder: isHebrew ? "סיסמה חדשה" : "New password",
    newNamePlaceholder: isHebrew ? "שם חדש" : "New name",
    updateNameError: isHebrew ? "עדכון השם נכשל." : "Failed to update name.",
    save: isHebrew ? "שמור" : "Save",
    assignGroup: isHebrew ? "שייך מדור" : "Assign Group",
    assignGroupTitle: isHebrew ? "שיוך מדור לוועידה" : "Assign Group to Meeting",
    selectGroup: isHebrew ? "בחר מדור..." : "Select group...",
    assign: isHebrew ? "שייך" : "Assign",
    removeAssign: isHebrew ? "הסר שיוך" : "Remove Assignment",
    assigning: isHebrew ? "משייך..." : "Assigning...",
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

  // שליפת קבוצות למיפוי UUID → שם
  const [groupMap, setGroupMap] = useState({});
  useEffect(() => {
    groupAPI.listGroups()
      .then((resp) => {
        const map = {};
        (resp.data || []).forEach((g) => {
          const key = String(g.UUID).toLowerCase();
          map[key] = g.name;
        });
        setGroupMap(map);
      })
      .catch(() => {});
  }, []);

  // חיפוש
  const [search, setSearch] = useState("");
  const [searchField, setSearchField] = useState("all");

  const searchPlaceholder =
    searchField === "name_or_number"
      ? text.searchPlaceholderNameOrNumber
      : searchField === "group"
        ? text.searchPlaceholderGroup
        : text.searchPlaceholderNameOrNumber;

  useEffect(() => { setPage(1); }, [search, searchField, sortField, sortDir]);

  const filtered = data.filter((m) => {
    if (searchField === "no_group") return !(m.groups?.length);
    if (searchField === "all") return true;
    const query = search.toLowerCase();
    if (!query) return false;
    if (searchField === "name_or_number") {
      const nameMatch = (m.name || "").toLowerCase().startsWith(query);
      const numberMatch = (m.meetingId || "").toLowerCase().startsWith(query);
      return nameMatch || numberMatch;
    }
    if (searchField === "group") {
      return (m.groups || []).some((g) => {
        const groupName = (groupMap[String(g).toLowerCase()] || "").toLowerCase();
        return groupName.startsWith(query);
      });
    }
    return true;
  }).sort((a, b) => {
    let av, bv;
    if (sortField === "number") {
      av = parseInt(a.meetingId) || 0;
      bv = parseInt(b.meetingId) || 0;
    } else if (sortField === "group") {
      av = (a.groups || []).map(g => groupMap[String(g).toLowerCase()] || "").join(",").toLowerCase();
      bv = (b.groups || []).map(g => groupMap[String(g).toLowerCase()] || "").join(",").toLowerCase();
    } else {
      av = a.meetingId || "";
      bv = b.meetingId || "";
    }
    if (av < bv) return sortDir === "asc" ? -1 : 1;
    if (av > bv) return sortDir === "asc" ? 1 : -1;
    return 0;
  });

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const paginated = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleOpenAssign = (meeting) => {
    setAssignGroupId("");
    setAssignError("");
    setAssignGroupModal(meeting);
  };

  const handleAssignGroup = async () => {
    if (!assignGroupModal || !assignGroupId) return;
    setAssignLoading(true);
    setAssignError("");
    try {
      await groupAPI.addMeeting(assignGroupId, assignGroupModal.dbId, assignGroupModal.accessLevel);
      setAssignGroupModal(null);
      showToast(isHebrew ? "שיוך המדור עודכן בהצלחה" : "Group assigned successfully");
      onRefresh();
    } catch (err) {
      setAssignError(err.response?.data?.detail || (isHebrew ? "שגיאה בשיוך" : "Assignment failed"));
    } finally {
      setAssignLoading(false);
    }
  };

  const handleRemoveAssign = async (groupUUID) => {
    if (!assignGroupModal) return;
    setAssignLoading(true);
    setAssignError("");
    try {
      await groupAPI.removeMeeting(groupUUID, assignGroupModal.dbId, assignGroupModal.accessLevel);
      setConfirmRemoveAssign(false);
      showToast(isHebrew ? "שיוך המדור הוסר בהצלחה" : "Group assignment removed", "info");
      onRefresh();
    } catch (err) {
      setAssignError(err.response?.data?.detail || (isHebrew ? "שגיאה בהסרה" : "Remove failed"));
    } finally {
      setAssignLoading(false);
    }
  };

  const handleFavoriteToggle = async (meeting) => {
    if (!meeting?.onToggleFavorite) return;
    setFavoriteBusyId(meeting.dbId);
    try {
      await meeting.onToggleFavorite(meeting);
      showToast(
        meeting.isFavorite
          ? (isHebrew ? "הוסר ממועדפים" : "Removed from favorites")
          : (isHebrew ? "נוסף למועדפים" : "Added to favorites"),
        meeting.isFavorite ? "info" : "success"
      );
    } finally {
      setFavoriteBusyId(null);
    }
  };

  const handleCreate = async () => {
    if (!mNumber.trim()) return;
    setCreating(true);
    setCreateError("");
    try {
      // הבאקנד יוצר גם ב-CMS (write-through) — אין צורך בקריאה נפרדת
      await meetingAPI.createMeeting({
        name: name.trim(),
        m_number: mNumber.trim(),
        accessLevel,
        ...(password.trim() ? { password: password.trim() } : {}),
      });
      setMNumber("");
      setName("");
      setPassword("");
      setShowCreate(false);
      if (onRefresh) onRefresh();
    } catch (err) {
      setCreateError(err.response?.data?.detail || text.createError);
    } finally {
      setCreating(false);
    }
  };

  const handleEditNameSave = async (meeting) => {
    const newName = editName.trim();
    if (!newName) return;
    setSavingName(true);
    setEditNameError("");
    try {
      await meetingAPI.updateMeetingName(meeting.dbId, newName, meeting.accessLevel);
      setEditNameId(null);
      setEditName("");
      showToast(isHebrew ? "שם עודכן בהצלחה" : "Name updated successfully");
      if (onRefresh) onRefresh();
    } catch (err) {
      setEditNameError(err.response?.data?.detail || text.updateNameError);
    } finally {
      setSavingName(false);
    }
  };

  const handleEditSave = async (meeting) => {
    setSaving(true);
    setEditError("");
    const newPassword = editPassword.trim() || null;
    try {
      // הבאקנד מעדכן גם ב-CMS (write-through) — אין צורך בקריאה נפרדת
      await meetingAPI.updateMeetingPassword(meeting.dbId, newPassword, meeting.accessLevel);
      setEditId(null);
      setEditPassword("");
      showToast(isHebrew ? "סיסמא עודכנה בהצלחה" : "Password updated successfully");
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
      // הבאקנד מוחק גם מה-CMS (write-through) — קריאה אחת מוחקת משני המקומות
      await meetingAPI.deleteMeeting(meetingToDelete.dbId);
      if (editId === meetingToDelete.dbId) {
        setEditId(null);
        setEditPassword("");
      }
      if (editNameId === meetingToDelete.dbId) {
        setEditNameId(null);
        setEditName("");
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
              placeholder={text.meetingNamePlaceholder}
              value={name}
              onChange={(e) => setName(e.target.value)}
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
            <select
              className="meetings-filter-select"
              value={searchField}
              onChange={(e) => { setSearchField(e.target.value); setSearch(""); }}
            >
              <option value="all">{text.searchByAll}</option>
              <option value="name_or_number">{text.searchByNameOrNumber}</option>
              <option value="group">{text.searchByGroup}</option>
              <option value="no_group">{text.searchByNoGroup}</option>
            </select>
            {searchField !== "no_group" && searchField !== "all" && (
              <input
                className="meetings-search-input"
                type="text"
                placeholder={searchPlaceholder}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            )}
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
              {paginated.map((meeting) => (
                <div key={meeting.id} className="meeting-item">
                  <div className="meeting-info">
                    <span className="meeting-id">
                      {meeting.name || `${text.meeting} #${meeting.meetingId || meeting.dbId?.slice(0, 8)}`}
                    </span>
                    {isAdmin && (
                      <span className="meeting-uuid">
                        {text.meetingNumber}: {meeting.meetingId || "—"}
                      </span>
                    )}
                    <span className="meeting-group">
                      {text.group}:{" "}
                      {meeting.groups?.length
                        ? meeting.groups.map(g => groupMap[String(g).toLowerCase()] || String(g).slice(0, 8) + "...").join(" | ")
                        : text.noGroup}
                    </span>
                    <span className="meeting-group">
                      👥 {meeting.participantCount ?? 0} {text.participants}
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
                    {canEditName && (
                      <button
                        className="meeting-edit-btn"
                        onClick={() => {
                          setEditNameId(meeting.dbId);
                          setEditName(meeting.name || "");
                          setEditNameError("");
                          setEditId(null);
                        }}
                      >
                        <span className="action-btn-content">
                          <span className="action-btn-icon"><EditIcon /></span>
                          <span>{text.editName}</span>
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
                            setEditNameId(null);
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
                    {(
                      <button
                        className="meeting-participants-btn"
                        onClick={() => handleViewParticipants(meeting)}
                      >
                        <span className="action-btn-content">
                          <span className="action-btn-icon">👥</span>
                          <span>{isHebrew ? "משתתפים" : "Participants"}</span>
                        </span>
                      </button>
                    )}
                    {isAdmin && (
                      <button
                        className="meeting-participants-btn"
                        onClick={() => handleOpenAssign(meeting)}
                      >
                        <span className="action-btn-content">
                          <span className="action-btn-icon">📁</span>
                          <span>{text.assignGroup}</span>
                        </span>
                      </button>
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
                  {canEditName && editNameId === meeting.dbId && (
                    <div className="meeting-edit-row">
                      <input
                        type="text"
                        placeholder={text.newNamePlaceholder}
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="meetings-create-input"
                      />
                      <button
                        className="meetings-create-submit"
                        onClick={() => handleEditNameSave(meeting)}
                        disabled={savingName}
                      >
                        {savingName ? text.saving : text.save}
                      </button>
                      <button
                        className="meeting-cancel-btn"
                        onClick={() => { setEditNameId(null); setEditName(""); }}
                      >
                        {text.cancel}
                      </button>
                      {editNameError && (
                        <span className="meetings-error">{editNameError}</span>
                      )}
                    </div>
                  )}
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
          {totalPages > 1 && (
            <div className="meetings-pagination">
              <button
                className="btn-ghost"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
              >
                ←
              </button>
              <span className="pagination-info">{page} / {totalPages}</span>
              <button
                className="btn-ghost"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
              >
                →
              </button>
            </div>
          )}
        </div>
      )}

      {participantsModal && (
        <div className="modal-overlay" onClick={() => setParticipantsModal(null)}>
          <div className="modal-card modal-card--wide" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">
              {isHebrew ? "משתתפים" : "Participants"} —{" "}
              {isHebrew ? "ועידה" : "Meeting"} #{participantsModal.meetingId}
            </h3>

            <div className="modal-tabs">
              <button
                className={`modal-tab${activeTab === "authorized" ? " active" : ""}`}
                onClick={() => handleTabChange("authorized", participantsModal)}
              >
                👥 {isHebrew ? "מורשים" : "Authorized"}
              </button>
              {isAdmin && (
                <button
                  className={`modal-tab${activeTab === "live" ? " active" : ""}`}
                  onClick={() => handleTabChange("live", participantsModal)}
                >
                  📡 {isHebrew ? "פעילים" : "Live"}
                </button>
              )}
            </div>

            {activeTab === "authorized" && (
              <>
                {participantsLoading ? (
                  <div className="logs-loading">{isHebrew ? "טוען..." : "Loading..."}</div>
                ) : participantsError ? (
                  <div className="meetings-error">{participantsError}</div>
                ) : participants.length === 0 ? (
                  <div className="meetings-empty">{isHebrew ? "אין משתמשים מורשים לוועידה זו" : "No authorized users for this meeting"}</div>
                ) : (
                  <table className="participants-table">
                    <thead>
                      <tr>
                        <th>{isHebrew ? "מספר זיהוי" : "S_ID"}</th>
                        <th>{isHebrew ? "שם משתמש" : "Username"}</th>
                        <th>{isHebrew ? "תפקיד" : "Role"}</th>
                        <th>{isHebrew ? "מדור" : "Group"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {participants.map((p, i) => (
                        <tr key={i}>
                          <td>{p.S_ID || "—"}</td>
                          <td>{p.username || "—"}</td>
                          <td>{p.role || "—"}</td>
                          <td>{p.group || "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </>
            )}

            {activeTab === "live" && (
              <>
                {liveLoading ? (
                  <div className="logs-loading">{isHebrew ? "טוען..." : "Loading..."}</div>
                ) : liveError ? (
                  <div className="meetings-error">{liveError}</div>
                ) : liveParticipants.length === 0 ? (
                  <div className="meetings-empty">
                    {isHebrew ? "אין משתתפים פעילים כרגע בשיחה" : "No active participants in this call"}
                  </div>
                ) : (
                  <table className="participants-table">
                    <thead>
                      <tr>
                        <th>{isHebrew ? "שם" : "Name"}</th>
                        <th>{isHebrew ? "סטטוס" : "State"}</th>
                        <th>{isHebrew ? "מושתק" : "Muted"}</th>
                        <th>{isHebrew ? "פעולות" : "Actions"}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {liveParticipants.map((p, i) => {
                        const legId = p.legId || p["@id"] || String(i);
                        const isMuted = p.mute === "true" || p.mute === true;
                        return (
                          <tr key={legId}>
                            <td>{p.name || p.remoteParty || "—"}</td>
                            <td>{p.state || p.status || "—"}</td>
                            <td>{isMuted ? "🔇" : "🔊"}</td>
                            <td className="participants-actions-cell">
                              <button
                                className={`participant-action-btn ${isMuted ? "unmute" : "mute"}`}
                                onClick={() => handleMute(legId, isMuted)}
                                disabled={muteLoadingId === legId}
                              >
                                {muteLoadingId === legId ? "..." : isMuted ? (isHebrew ? "בטל השתקה" : "Unmute") : (isHebrew ? "השתק" : "Mute")}
                              </button>
                              <button
                                className="participant-action-btn kick"
                                onClick={() => handleKick(legId)}
                                disabled={kickLoadingId === legId}
                              >
                                {kickLoadingId === legId ? "..." : (isHebrew ? "הסר" : "Kick")}
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </>
            )}

            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setParticipantsModal(null)}>
                {isHebrew ? "סגור" : "Close"}
              </button>
              {activeTab === "live" && (
                <button className="btn-secondary" onClick={() => handleLoadLive(participantsModal)}>
                  {isHebrew ? "רענן" : "Refresh"}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {assignGroupModal && (
        <div className="modal-overlay" onClick={() => setAssignGroupModal(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">
              {text.assignGroupTitle} — #{assignGroupModal.meetingId}
            </h3>
            <div style={{ marginBottom: "16px" }}>
              <select
                className="meetings-filter-select"
                style={{ width: "100%", marginBottom: "12px" }}
                value={assignGroupId}
                onChange={(e) => setAssignGroupId(e.target.value)}
                disabled={assignLoading}
              >
                <option value="">{text.selectGroup}</option>
                {Object.entries(groupMap).map(([uuid, name]) => (
                  <option key={uuid} value={uuid}>{name}</option>
                ))}
              </select>
            </div>
            {assignGroupModal.groups?.length > 0 && (
              <div style={{ marginBottom: "16px" }}>
                <div style={{ fontSize: "0.85rem", marginBottom: "6px", fontWeight: 500 }}>
                  {isHebrew ? "מדורים משויכים:" : "Assigned groups:"}
                </div>
                {assignGroupModal.groups.map((g) => {
                  const gKey = String(g).toLowerCase();
                  const gName = groupMap[gKey] || gKey.slice(0, 8) + "...";
                  return (
                    <div key={g} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span>{gName}</span>
                      <button className="btn-danger" style={{ padding: "2px 8px", fontSize: "0.8rem" }}
                        onClick={() => handleRemoveAssign(gKey)} disabled={assignLoading}>
                        {isHebrew ? "הסר" : "Remove"}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
            {assignError && (
              <div className="meetings-error" style={{ marginBottom: "12px" }}>{assignError}</div>
            )}
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setAssignGroupModal(null)} disabled={assignLoading}>
                {text.cancel}
              </button>
              <button className="btn-primary" onClick={handleAssignGroup} disabled={assignLoading || !assignGroupId}>
                {assignLoading ? text.assigning : text.assign}
              </button>
            </div>
          </div>
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
      {toast && (
        <div className={`toast-notification toast-${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
