import { useCallback, useEffect, useState } from "react";
import { favoriteAPI, groupAPI, meetingAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import LiveActivityChart from "../components/LiveActivityChart";
import "../components/MeetingsPage.css";
import "./Dashboard.css";

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
      <path d="M12 20h9" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
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

export default function Dashboard({ language = "en" }) {
  const isHebrew = language === "he";
  const { currentUser } = useAuth();
  const userRole = currentUser?.role?.toLowerCase() || "";
  const isAdmin = userRole === "admin" || userRole === "super_admin";
  const isStaff = isAdmin || userRole === "agent";
  const canEditPassword = isAdmin;
  const canEditName = isAdmin;

  const [favorites, setFavorites] = useState([]);
  const [favLoading, setFavLoading] = useState(true);
  const [favError, setFavError] = useState("");

  const [groupMap, setGroupMap] = useState({});
  const [editId, setEditId] = useState(null);
  const [editPassword, setEditPassword] = useState("");
  const [editError, setEditError] = useState("");
  const [saving, setSaving] = useState(false);
  const [editNameId, setEditNameId] = useState(null);
  const [editName, setEditName] = useState("");
  const [editNameError, setEditNameError] = useState("");
  const [savingName, setSavingName] = useState(false);
  const [participantsModal, setParticipantsModal] = useState(null);
  const [participantsLoading, setParticipantsLoading] = useState(false);
  const [participantsError, setParticipantsError] = useState("");
  const [participants, setParticipants] = useState([]);
  const [activeTab, setActiveTab] = useState("authorized");
  const [liveParticipantsLoading, setLiveParticipantsLoading] = useState(false);
  const [liveParticipantsError, setLiveParticipantsError] = useState("");
  const [liveParticipants, setLiveParticipants] = useState([]);
  const [liveCallId, setLiveCallId] = useState(null);
  const [muteLoadingId, setMuteLoadingId] = useState(null);
  const [kickLoadingId, setKickLoadingId] = useState(null);
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

  const [liveStats, setLiveStats] = useState({
    total_active: 0,
    by_type: {
      audio: { meetings: 0, participants: 0 },
      video: { meetings: 0, participants: 0 },
      blast_dial: { meetings: 0, participants: 0 },
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
      showToast(isHebrew ? "הוסר ממועדפים" : "Removed from favorites", "info");
    } catch (err) {
      setFavError(err.response?.data?.detail || "Failed to remove favorite.");
    }
  };

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

  const handleEditNameSave = async (meeting) => {
    const newName = editName.trim();
    if (!newName) return;
    setSavingName(true);
    setEditNameError("");
    try {
      await meetingAPI.updateMeetingName(meeting.m_number, newName, meeting.accessLevel);
      setEditNameId(null);
      setEditName("");
      showToast(isHebrew ? "שם עודכן בהצלחה" : "Name updated successfully");
      await loadFavorites();
    } catch (err) {
      setEditNameError(err.response?.data?.detail || (isHebrew ? "עדכון השם נכשל" : "Failed to update name"));
    } finally {
      setSavingName(false);
    }
  };

  const handleEditSave = async (meeting) => {
    setSaving(true);
    setEditError("");
    try {
      await meetingAPI.updateMeetingPassword(meeting.m_number, editPassword.trim() || null, meeting.accessLevel);
      setEditId(null);
      setEditPassword("");
      showToast(isHebrew ? "סיסמא עודכנה בהצלחה" : "Password updated successfully");
      await loadFavorites();
      await loadLiveStats();
    } catch (err) {
      setEditError(err.response?.data?.detail || (isHebrew ? "עדכון הסיסמה נכשל" : "Failed to update password"));
    } finally {
      setSaving(false);
    }
  };

  const handleViewParticipants = async (meeting) => {
    setParticipantsModal(meeting);
    setActiveTab("authorized");
    setParticipants([]);
    setParticipantsError("");
    setLiveParticipants([]);
    setLiveCallId(null);
    setLiveParticipantsError("");
    setParticipantsLoading(true);
    try {
      const resp = await meetingAPI.getParticipants(meeting.m_number);
      setParticipants(resp.data.participants || []);
    } catch {
      setParticipantsError(isHebrew ? "טעינת משתתפים נכשלה" : "Failed to load participants");
    } finally {
      setParticipantsLoading(false);
    }
  };

  const handleLoadLive = async (meeting) => {
    setLiveParticipants([]);
    setLiveCallId(null);
    setLiveParticipantsError("");
    setLiveParticipantsLoading(true);
    try {
      const resp = await meetingAPI.getLiveParticipants(meeting.m_number);
      setLiveParticipants(resp.data.participants || []);
      setLiveCallId(resp.data.call_id || null);
    } catch {
      setLiveParticipantsError(isHebrew ? "טעינת משתתפים חיים נכשלה" : "Failed to load live participants");
    } finally {
      setLiveParticipantsLoading(false);
    }
  };

  const handleTabChange = (tab, meeting) => {
    setActiveTab(tab);
    if (tab === "live" && liveParticipants.length === 0 && !liveParticipantsLoading) {
      handleLoadLive(meeting);
    }
  };

  const handleMute = async (legId, currentMute) => {
    if (!participantsModal) return;
    setMuteLoadingId(legId);
    try {
      await meetingAPI.muteParticipant(participantsModal.m_number, liveCallId, legId, !currentMute);
      setLiveParticipants((prev) =>
        prev.map((p) =>
          (p.legId || p["@id"]) === legId ? { ...p, mute: (!currentMute).toString() } : p
        )
      );
    } catch {
      setLiveParticipantsError(isHebrew ? "פעולת השתקה נכשלה" : "Mute action failed");
    } finally {
      setMuteLoadingId(null);
    }
  };

  const handleKick = async (legId) => {
    if (!participantsModal) return;
    setKickLoadingId(legId);
    try {
      await meetingAPI.kickParticipant(participantsModal.m_number, liveCallId, legId);
      setLiveParticipants((prev) => prev.filter((p) => (p.legId || p["@id"]) !== legId));
    } catch {
      setLiveParticipantsError(isHebrew ? "פעולת ההסרה נכשלה" : "Kick action failed");
    } finally {
      setKickLoadingId(null);
    }
  };

  const handleOpenAssign = (meeting) => {
    const currentGroupKey = meeting.groups?.[0]
      ? String(meeting.groups[0]).toLowerCase()
      : "";
    setAssignGroupId(currentGroupKey);
    setAssignError("");
    setConfirmRemoveAssign(false);
    setAssignGroupModal(meeting);
  };

  const handleAssignGroup = async () => {
    if (!assignGroupModal) return;
    setAssignLoading(true);
    setAssignError("");
    try {
      const currentGroupKey = assignGroupModal.groups?.[0]
        ? String(assignGroupModal.groups[0]).toLowerCase()
        : "";
      if (currentGroupKey && currentGroupKey !== assignGroupId) {
        await groupAPI.removeMeeting(currentGroupKey, assignGroupModal.m_number);
      }
      if (assignGroupId) {
        const targetUUID = Object.keys(groupMap).find((k) => k === assignGroupId);
        if (targetUUID) await groupAPI.addMeeting(targetUUID, assignGroupModal.m_number);
      }
      setAssignGroupModal(null);
      showToast(isHebrew ? "שיוך המדור עודכן בהצלחה" : "Group assigned successfully");
      await loadFavorites();
      await loadLiveStats();
    } catch (err) {
      setAssignError(err.response?.data?.detail || (isHebrew ? "שגיאה בשיוך" : "Assignment failed"));
    } finally {
      setAssignLoading(false);
    }
  };

  const handleRemoveAssign = async () => {
    if (!assignGroupModal?.groups?.[0]) return;
    setAssignLoading(true);
    setAssignError("");
    try {
      const currentGroupKey = String(assignGroupModal.groups[0]).toLowerCase();
      await groupAPI.removeMeeting(currentGroupKey, assignGroupModal.m_number);
      setAssignGroupModal(null);
      setConfirmRemoveAssign(false);
      showToast(isHebrew ? "שיוך המדור הוסר בהצלחה" : "Group assignment removed", "info");
      await loadFavorites();
      await loadLiveStats();
    } catch (err) {
      setAssignError(err.response?.data?.detail || (isHebrew ? "שגיאה בהסרה" : "Remove failed"));
    } finally {
      setAssignLoading(false);
    }
  };

  const loadLiveStats = useCallback(async () => {
    try {
      setLiveLoading(true);
      setLiveError("");
      setLiveWarning("");

      const allTypes = ["audio", "video", "blast_dial"];
      const allowedTypes = (() => {
        if (userRole !== "admin") return allTypes;
        const list = [];
        if (currentUser?.can_audio) list.push("audio");
        if (currentUser?.can_video) list.push("video");
        return list;
      })();

      const resultsByType = Object.fromEntries(
        allTypes.map((t) => [t, { status: "fulfilled", value: { data: [] } }])
      );
      const requests = allowedTypes.map((t) =>
        meetingAPI.getAllMeetings(t).then((res) => ({ type: t, res }))
      );
      const settled = await Promise.allSettled(requests);
      settled.forEach((r) => {
        if (r.status === "fulfilled") {
          resultsByType[r.value.type] = { status: "fulfilled", value: r.value.res };
        }
      });

      const dbStats = {
        audio: { meetings: 0, participants: 0 },
        video: { meetings: 0, participants: 0 },
        blast_dial: { meetings: 0, participants: 0 },
      };
      allTypes.forEach((type) => {
        const result = resultsByType[type];
        if (result.status === "fulfilled" && Array.isArray(result.value.data)) {
          dbStats[type].meetings = result.value.data.length;
        }
      });

      let cmsStats = null;
      let cmsWarning = "";
      try {
        const cmsResponse = await meetingAPI.getLiveStatus();
        cmsStats = cmsResponse.data?.by_type || null;
      } catch (cmsErr) {
        if (cmsErr.response?.status === 403) {
          cmsWarning = isHebrew
            ? "נתוני CMS מוגבלים להרשאות גבוהות"
            : "CMS live data requires elevated permissions";
        } else {
          cmsWarning = isHebrew
            ? "CMS לא זמין"
            : "CMS is unreachable";
        }
      }

      const stats = {
        audio: {
          meetings: dbStats.audio.meetings,
          participants: cmsStats?.audio?.participants ?? 0,
        },
        video: {
          meetings: dbStats.video.meetings,
          participants: cmsStats?.video?.participants ?? 0,
        },
        blast_dial: {
          meetings: dbStats.blast_dial.meetings,
          participants: cmsStats?.blast_dial?.participants ?? 0,
        },
      };

      const totalActive =
        (stats.audio.meetings || 0) +
        (stats.video.meetings || 0) +
        (stats.blast_dial.meetings || 0);

      setLiveStats({
        total_active: totalActive,
        by_type: stats,
      });
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
    const refresh = () => { loadLiveStats(); loadFavorites(); };
    refresh();
    const interval = setInterval(refresh, 30000);
    const onVisible = () => { if (document.visibilityState === "visible") loadFavorites(); };
    document.addEventListener("visibilitychange", onVisible);
    return () => { clearInterval(interval); document.removeEventListener("visibilitychange", onVisible); };
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
        meeting: "ועידה",
        refresh: "רענן",
        loading: "טוען...",
        saved: "שמורות",
        noFavorites: "אין ועידות מועדפות עדיין.",
        noParticipants: "אין משתתפים",
        noPassword: "ללא סיסמה",
        noGroup: "ללא מדור",
        remove: "הסר",
        removeFavorite: "הסר",
        editName: "שם",
        editPassword: "סיסמה",
        participants: "משתתפים",
        authorized: "מורשים",
        live: "פעילים",
        assignGroup: "מדור",
        assignGroupTitle: "שיוך מדור",
        selectGroup: "בחר מדור...",
        assign: "שייך",
        removeAssign: "הסר שיוך",
        saving: "שומר...",
        assigning: "משייך...",
        cancel: "ביטול",
        save: "שמור",
        close: "סגור",
        noAuthorizedUsers: "אין משתמשים מורשים",
        noLiveParticipants: "אין משתתפים פעילים",
        name: "שם",
        username: "שם משתמש",
        role: "תפקיד",
        group: "מדור",
        state: "סטטוס",
        muted: "מושתק",
        actions: "פעולות",
        mute: "השתק",
        unmute: "בטל השתקה",
        kick: "הסר",
        sure: "בטוח?",
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
        meeting: "Meeting",
        refresh: "Refresh",
        loading: "Loading...",
        saved: "saved",
        noFavorites: "No favorites yet.",
        noParticipants: "No participants",
        noPassword: "No password",
        noGroup: "No group",
        remove: "Remove",
        removeFavorite: "Remove",
        editName: "Name",
        editPassword: "Password",
        participants: "Participants",
        authorized: "Authorized",
        live: "Live",
        assignGroup: "Group",
        assignGroupTitle: "Assign Group",
        selectGroup: "Select group...",
        assign: "Assign",
        removeAssign: "Remove",
        saving: "Saving...",
        assigning: "Assigning...",
        cancel: "Cancel",
        save: "Save",
        close: "Close",
        noAuthorizedUsers: "No authorized users",
        noLiveParticipants: "No active participants",
        name: "Name",
        username: "Username",
        role: "Role",
        group: "Group",
        state: "State",
        muted: "Muted",
        actions: "Actions",
        mute: "Mute",
        unmute: "Unmute",
        kick: "Kick",
        sure: "Sure?",
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
                        key={meeting.m_number}
                        className={`meeting-item fav-meeting-item fav-type-${(meeting.accessLevel).toLowerCase()}`}
                      >
                        <div className="fav-meeting-accent"></div>
                        <div className="fav-meeting-main">
                          <div className="fav-meeting-header">
                            <span className="fav-meeting-id">
                              #{meeting.m_number}{meeting.name ? ` — ${meeting.name}` : ""}
                            </span>
                            <span className="fav-meeting-type">
                              {meeting.accessLevel || "—"}
                            </span>
                          </div>
                          <div className="fav-meeting-details">
                            <span className="fav-meeting-group">
                              {labels.group}: {" "}
                              {meeting.groups?.length
                                ? meeting.groups.map(g => groupMap[String(g).toLowerCase()] || String(g).slice(0, 8) + "...").join(" | ")
                                : labels.noGroup}
                            </span>
                            <span className="fav-meeting-pass">
                              {meeting.password || labels.noPassword}
                            </span>
                            <span className="fav-meeting-participants">
                              {(meeting.participants || []).length > 0
                                ? `${(meeting.participants || []).length} ${labels.participantsCount}`
                                : labels.noParticipants}
                            </span>
                          </div>
                          <div className="fav-meeting-actions">
                            <button
                              className="meeting-favorite-btn active"
                              onClick={() => handleRemoveFavorite(meeting.m_number)}
                            >
                              <span className="action-btn-content">
                                <span className="action-btn-icon"><FavoriteIcon /></span>
                                <span>{labels.removeFavorite}</span>
                              </span>
                            </button>
                            {canEditName && String(meeting.accessLevel).toLowerCase() !== "audio" && (
                              <button
                                className="meeting-edit-btn"
                                onClick={() => {
                                  setEditNameId(meeting.m_number);
                                  setEditName(meeting.name || "");
                                  setEditNameError("");
                                  setEditId(null);
                                }}
                              >
                                <span className="action-btn-content">
                                  <span className="action-btn-icon"><EditIcon /></span>
                                  <span>{labels.editName}</span>
                                </span>
                              </button>
                            )}
                            {canEditPassword && (
                              <button
                                className="meeting-edit-btn"
                                onClick={() => {
                                  setEditId(meeting.m_number);
                                  setEditPassword(meeting.password || "");
                                  setEditError("");
                                  setEditNameId(null);
                                }}
                              >
                                <span className="action-btn-content">
                                  <span className="action-btn-icon"><EditIcon /></span>
                                  <span>{labels.editPassword}</span>
                                </span>
                              </button>
                            )}
                            <button
                              className="meeting-participants-btn"
                              onClick={() => handleViewParticipants(meeting)}
                            >
                              <span className="action-btn-content">
                                <span className="action-btn-icon">👥</span>
                                <span>{labels.participants}</span>
                              </span>
                            </button>
                            {isAdmin && (
                              <button
                                className="meeting-participants-btn"
                                onClick={() => handleOpenAssign(meeting)}
                              >
                                <span className="action-btn-content">
                                  <span className="action-btn-icon">📁</span>
                                  <span>{labels.assignGroup}</span>
                                </span>
                              </button>
                            )}
                          </div>
                          {canEditName && editNameId === meeting.m_number && (
                            <div className="meeting-edit-row">
                              <input
                                type="text"
                                placeholder={isHebrew ? "שם חדש" : "New name"}
                                value={editName}
                                onChange={(e) => setEditName(e.target.value)}
                                className="meetings-create-input"
                              />
                              <button
                                className="meetings-create-submit"
                                onClick={() => handleEditNameSave(meeting)}
                                disabled={savingName}
                              >
                                {savingName ? labels.saving : labels.save}
                              </button>
                              <button
                                className="meeting-cancel-btn"
                                onClick={() => { setEditNameId(null); setEditName(""); }}
                              >
                                {labels.cancel}
                              </button>
                              {editNameError && <span className="meetings-error">{editNameError}</span>}
                            </div>
                          )}
                          {canEditPassword && editId === meeting.m_number && (
                            <div className="meeting-edit-row">
                              <input
                                type="text"
                                placeholder={isHebrew ? "סיסמה חדשה" : "New password"}
                                value={editPassword}
                                onChange={(e) => setEditPassword(e.target.value)}
                                className="meetings-create-input"
                              />
                              <button
                                className="meetings-create-submit"
                                onClick={() => handleEditSave(meeting)}
                                disabled={saving}
                              >
                                {saving ? labels.saving : labels.save}
                              </button>
                              <button
                                className="meeting-cancel-btn"
                                onClick={() => {
                                  setEditId(null);
                                  setEditPassword("");
                                  setEditError("");
                                }}
                              >
                                {labels.cancel}
                              </button>
                              {editError && <span className="meetings-error">{editError}</span>}
                            </div>
                          )}
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

      {participantsModal && (
        <div className="modal-overlay" onClick={() => setParticipantsModal(null)}>
          <div className="modal-card modal-card--wide" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">
              {labels.participants} — {labels.meeting} #{participantsModal.m_number}
            </h3>

            <div className="modal-tabs">
              <button
                className={`modal-tab${activeTab === "authorized" ? " active" : ""}`}
                onClick={() => handleTabChange("authorized", participantsModal)}
              >
                👥 {labels.authorized}
              </button>
              {isStaff && (
                <button
                  className={`modal-tab${activeTab === "live" ? " active" : ""}`}
                  onClick={() => handleTabChange("live", participantsModal)}
                >
                  📡 {labels.live}
                </button>
              )}
            </div>

            {activeTab === "authorized" && (
              <>
                {participantsLoading ? (
                  <div className="logs-loading">{labels.loading}</div>
                ) : participantsError ? (
                  <div className="meetings-error">{participantsError}</div>
                ) : participants.length === 0 ? (
                  <div className="meetings-empty">{labels.noAuthorizedUsers}</div>
                ) : (
                  <table className="participants-table">
                    <thead>
                      <tr>
                        <th>{labels.username}</th>
                        <th>{labels.role}</th>
                        <th>{labels.group}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {participants.map((p, i) => (
                        <tr key={i}>
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
                {liveParticipantsLoading ? (
                  <div className="logs-loading">{labels.loading}</div>
                ) : liveParticipantsError ? (
                  <div className="meetings-error">{liveParticipantsError}</div>
                ) : liveParticipants.length === 0 ? (
                  <div className="meetings-empty">{labels.noLiveParticipants}</div>
                ) : (
                  <table className="participants-table">
                    <thead>
                      <tr>
                        <th>{labels.name}</th>
                        <th>{labels.state}</th>
                        <th>{labels.muted}</th>
                        {isStaff && <th>{labels.actions}</th>}
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
                            {isStaff && (
                              <td className="participants-actions-cell">
                                <button
                                  className={`participant-action-btn ${isMuted ? "unmute" : "mute"}`}
                                  onClick={() => handleMute(legId, isMuted)}
                                  disabled={muteLoadingId === legId}
                                >
                                  {muteLoadingId === legId
                                    ? "..."
                                    : isMuted
                                      ? labels.unmute
                                      : labels.mute}
                                </button>
                                <button
                                  className="participant-action-btn kick"
                                  onClick={() => handleKick(legId)}
                                  disabled={kickLoadingId === legId}
                                >
                                  {kickLoadingId === legId ? "..." : labels.kick}
                                </button>
                              </td>
                            )}
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
                {labels.close}
              </button>
              {activeTab === "live" && (
                <button className="btn-secondary" onClick={() => handleLoadLive(participantsModal)}>
                  {labels.refresh}
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
              {labels.assignGroupTitle} — #{assignGroupModal.m_number}
            </h3>
            <div style={{ marginBottom: "16px" }}>
              <select
                className="meetings-filter-select"
                style={{ width: "100%", marginBottom: "12px" }}
                value={assignGroupId}
                onChange={(e) => setAssignGroupId(e.target.value)}
                disabled={assignLoading}
              >
                <option value="">{labels.selectGroup}</option>
                {Object.entries(groupMap).map(([uuid, name]) => (
                  <option key={uuid} value={uuid}>{name}</option>
                ))}
              </select>
            </div>
            {assignError && (
              <div className="meetings-error" style={{ marginBottom: "12px" }}>{assignError}</div>
            )}
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setAssignGroupModal(null)} disabled={assignLoading}>
                {labels.cancel}
              </button>
              {assignGroupModal.groups?.[0] && !confirmRemoveAssign && (
                <button className="btn-danger" onClick={() => setConfirmRemoveAssign(true)} disabled={assignLoading}>
                  {labels.removeAssign}
                </button>
              )}
              {assignGroupModal.groups?.[0] && confirmRemoveAssign && (
                <>
                  <span style={{ fontSize: "0.85rem", color: "#d32f2f", alignSelf: "center" }}>
                    {labels.sure}
                  </span>
                  <button className="btn-danger" onClick={handleRemoveAssign} disabled={assignLoading}>
                    {assignLoading ? labels.assigning : (isHebrew ? "כן, הסר" : "Yes, remove")}
                  </button>
                  <button className="btn-secondary" onClick={() => setConfirmRemoveAssign(false)} disabled={assignLoading}>
                    {labels.cancel}
                  </button>
                </>
              )}
              <button className="btn-primary" onClick={handleAssignGroup} disabled={assignLoading || !assignGroupId}>
                {assignLoading ? labels.assigning : labels.assign}
              </button>
            </div>
          </div>
        </div>
      )}


      {toast && (
        <div className={`toast-notification toast-${toast.type}`}>
          {toast.message}
        </div>
      )}
    </div>
  );
}
