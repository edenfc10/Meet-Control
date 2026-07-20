// Groups Page - ניהול קבוצות
// תומך ב: יצירה, מחיקה, עריכת שם, ניהול חברים + access_level, שיוך פגישות

import { useEffect, useMemo, useState } from "react";
import { groupAPI, userAPI, meetingAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import GroupMembersPanel from "../components/GroupMembersPanel";
import GroupMeetingsPanel from "../components/GroupMeetingsPanel";
import "./Groups.css";

export default function Groups({ language = "en" }) {
  const { currentUser } = useAuth();
  const isHebrew = language === "he";
  const role = currentUser?.role;
  const isAdmin = role === "admin" || role === "super_admin";
  const canReadAllUsers = isAdmin;

  const text = {
    pageTitle: isHebrew ? "מדורים" : "Groups",
    createTitle: isHebrew ? "יצירת מדור" : "Create Group",
    createPlaceholder: isHebrew ? "הכנס שם מדור" : "Enter group name",
    creating: isHebrew ? "יוצר..." : "Creating...",
    createButton: isHebrew ? "צור מדור" : "Create Group",
    loadGroupsError: isHebrew
      ? "טעינת המדורים נכשלה."
      : "Failed to load groups.",
    createGroupError: isHebrew
      ? "יצירת המדור נכשלה."
      : "Failed to create group.",
    deleteConfirm: isHebrew
      ? "האם אתה בטוח שברצונך למחוק מדור זה?"
      : "Are you sure you want to delete this group?",
    deleteGroupModalTitle: isHebrew ? "מחיקת מדור" : "Delete Group",
    deleteGroupModalMessage: isHebrew
      ? "האם אתה בטוח שברצונך למחוק את המדור"
      : "Are you sure you want to delete the group",
    deletingGroup: isHebrew ? "מוחק..." : "Deleting...",
    deleteGroupError: isHebrew
      ? "מחיקת המדור נכשלה."
      : "Failed to delete group.",
    updateGroupError: isHebrew
      ? "עדכון המדור נכשל."
      : "Failed to update group.",
    loadGroupDataError: isHebrew
      ? "טעינת נתוני המדור נכשלה."
      : "Failed to load group data.",
    allGroups: isHebrew ? "כל המדורים" : "All Groups",
    of: isHebrew ? "מתוך" : "of",
    searchGroupPlaceholder: isHebrew
      ? "חיפוש לפי שם מדור..."
      : "Search by group name...",
    refresh: isHebrew ? "רענון" : "Refresh",
    groupsHint: isHebrew
      ? 'לחץ על "ניהול" כדי לצפות ולנהל חברי מדור וועידות.'
      : 'Click "Manage" to view and manage group members and meetings.',
    loadingGroups: isHebrew ? "טוען מדורים..." : "Loading groups...",
    noGroups: isHebrew ? "לא נמצאו מדורים." : "No groups found.",
    noGroupsMatch: isHebrew
      ? "לא נמצאו מדורים שמתאימים לחיפוש."
      : "No groups match your search.",
    save: isHebrew ? "שמור" : "Save",
    cancel: isHebrew ? "ביטול" : "Cancel",
    members: isHebrew ? "חברים" : "Members",
    meetings: isHebrew ? "הוספת ועידות" : "Add Meetings",
    manage: isHebrew ? "ניהול" : "Manage",
    editName: isHebrew ? "ערוך שם" : "Edit Name",
    delete: isHebrew ? "מחיקה" : "Delete",
    manageTitle: isHebrew ? "קבוצה" : "Group",
    loading: isHebrew ? "טוען..." : "Loading...",
    currentMembers: isHebrew ? "חברים נוכחיים" : "Current Members",
    noMembers: isHebrew ? "עדיין אין חברים." : "No members yet.",
    username: isHebrew ? "שם משתמש" : "Username",
    tableRole: isHebrew ? "תפקיד" : "Role",
    meetingTypes: isHebrew ? "סוגי ועידה" : "Meeting Types",
    noAccessLevels: isHebrew ? "אין הרשאות" : "No access levels",
    removeUser: isHebrew ? "הסר משתמש" : "Remove User",
    removeMemberModalTitle: isHebrew
      ? "הסרת שיוך משתמש מהמדור"
      : "Remove User Assignment",
    removeMemberModalMessage: isHebrew
      ? "האם אתה בטוח שברצונך להסיר את המשתמש"
      : "Are you sure you want to remove user",
    removingUser: isHebrew ? "מסיר..." : "Removing...",
    addMember: isHebrew ? "הוספת חבר" : "Add Member",
    agentsOnly: isHebrew ? " (Agents בלבד)" : " (Agents only)",
    agentOnly: isHebrew ? " (Agent בלבד)" : " (Agents only)",
    noUsersToAdd: isHebrew
      ? "אין משתמשים זמינים להוספה."
      : "No users available to add.",
    searchUserPlaceholder: isHebrew
      ? "חיפוש משתמש ברשימה..."
      : "Search user in list...",
    searchUsersAria: isHebrew ? "חיפוש משתמשים" : "Search users",
    addableUsersAria: isHebrew ? "משתמשים זמינים להוספה" : "Addable users",
  };

  // קבוצות
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // חיפוש
  const [search, setSearch] = useState("");

  const filteredGroups = useMemo(() => {
    const q = search.trim().toLowerCase();
    return groups.filter((g) => {
      const matchName = !q || (g.name || "").toLowerCase().includes(q);
      return matchName;
    });
  }, [groups, search]);

  // יצירת קבוצה
  const [newGroupName, setNewGroupName] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");

  // עריכת קבוצה
  const [editingGroup, setEditingGroup] = useState(null);
  const [editName, setEditName] = useState("");

  // modal ניהול
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [modalMembers, setModalMembers] = useState([]);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState("");
  const [showDeleteGroupConfirm, setShowDeleteGroupConfirm] = useState(false);
  const [groupToDelete, setGroupToDelete] = useState(null);
  const [deleteGroupLoading, setDeleteGroupLoading] = useState(false);

  // נתוני חברים ופגישות (מועברים לפאנלים)
  const [allUsers, setAllUsers] = useState([]);
  const [allMeetings, setAllMeetings] = useState([]);

  const getGroupMemberCount = (group) => {
    const memberIds = (group?.members || []).map((member) => String(member));

    if (memberIds.length > 0) {
      return new Set(memberIds).size;
    }

    const accessRows = group?.member_access_levels || [];
    return new Set(accessRows.map((row) => String(row.user_id))).size;
  };

  // --- טעינת כל הקבוצות ---
  const fetchGroups = async () => {
    try {
      setError("");
      const resp = await groupAPI.listGroups();
      setGroups(resp.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || text.loadGroupsError);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  // --- יצירת קבוצה ---
  const handleCreate = async () => {
    if (!newGroupName.trim()) return;
    setCreateLoading(true);
    setCreateError("");
    try {
      await groupAPI.createGroup({ name: newGroupName.trim() });
      setNewGroupName("");
      await fetchGroups();
    } catch (err) {
      setCreateError(err.response?.data?.detail || text.createGroupError);
    } finally {
      setCreateLoading(false);
    }
  };

  // --- מחיקת קבוצה ---
  const handleDelete = (group) => {
    setGroupToDelete(group);
    setShowDeleteGroupConfirm(true);
  };

  const closeDeleteGroupConfirm = () => {
    if (deleteGroupLoading) return;
    setShowDeleteGroupConfirm(false);
    setGroupToDelete(null);
  };

  const confirmDeleteGroup = async () => {
    if (!groupToDelete) return;

    setDeleteGroupLoading(true);
    try {
      await groupAPI.deleteGroup(groupToDelete.UUID);
      closeDeleteGroupConfirm();
      await fetchGroups();
    } catch (err) {
      setError(err.response?.data?.detail || text.deleteGroupError);
    } finally {
      setDeleteGroupLoading(false);
    }
  };

  // --- עדכון שם קבוצה ---
  const handleUpdate = async (groupUUID) => {
    if (!editName.trim()) return;
    try {
      await groupAPI.updateGroup(groupUUID, { name: editName.trim() });
      setEditingGroup(null);
      setEditName("");
      await fetchGroups();
    } catch (err) {
      setError(err.response?.data?.detail || text.updateGroupError);
    }
  };

  // --- פתיחת modal ניהול ---
  const openModal = async (group) => {
    setSelectedGroup(group);
    setModalLoading(true);
    setModalError("");
    setModalMembers([]);
    try {
      const [membersResp, usersResp, meetingsResp] = await Promise.allSettled([
        groupAPI.getGroupMembers(group.UUID),
        canReadAllUsers ? userAPI.getAllUsers() : Promise.resolve({ data: [] }),
        meetingAPI.getAllMeetings(),
      ]);
      setModalMembers(membersResp.status === "fulfilled" ? membersResp.value.data || [] : []);
      setAllUsers(usersResp.status === "fulfilled" ? usersResp.value.data || [] : []);
      setAllMeetings(meetingsResp.status === "fulfilled" ? meetingsResp.value.data || [] : []);
      const firstError = [membersResp, usersResp, meetingsResp].find((r) => r.status === "rejected");
      if (firstError) {
        const msg = firstError.reason?.response?.data?.detail;
        if (msg) setModalError(msg);
      }
    } catch (err) {
      setModalError(text.loadGroupDataError);
    } finally {
      setModalLoading(false);
    }
  };

  const closeModal = () => {
    setSelectedGroup(null);
    setModalMembers([]);
    setModalError("");
    setAllUsers([]);
    setAllMeetings([]);
  };

  return (
    <div className="page groups-page">
      <h2 className="page-header">{text.pageTitle}</h2>

      {/* כרטיס יצירת קבוצה — admin/super_admin בלבד */}
      {isAdmin && (
        <section className="card groups-create-card">
          <h3>{text.createTitle}</h3>
          <div className="groups-create-row">
            <input
              className="groups-input"
              type="text"
              placeholder={text.createPlaceholder}
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
            <button
              className="btn-primary"
              onClick={handleCreate}
              disabled={createLoading || !newGroupName.trim()}
            >
              {createLoading ? text.creating : text.createButton}
            </button>
          </div>
          {createError && <div className="groups-error">{createError}</div>}
        </section>
      )}

      {/* רשימת קבוצות */}
      <section className="card groups-list-card">
        <h3>
          {text.allGroups} ({filteredGroups.length}
          {filteredGroups.length !== groups.length
            ? ` ${text.of} ${groups.length}`
            : ""}
          )
        </h3>

        <div className="users-filter-row">
          <input
            className="search-input"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={text.searchGroupPlaceholder}
          />
          <button
            className="btn-secondary refresh-soft-button"
            type="button"
            onClick={() => {
              setSearch("");
              fetchGroups();
            }}
          >
            {text.refresh}
          </button>
        </div>

        <p className="groups-hint">{text.groupsHint}</p>

        {loading ? (
          <div className="groups-empty">{text.loadingGroups}</div>
        ) : error ? (
          <div className="groups-error">{error}</div>
        ) : filteredGroups.length === 0 ? (
          <div className="groups-empty">
            {groups.length === 0 ? text.noGroups : text.noGroupsMatch}
          </div>
        ) : (
          <div className="groups-list">
            {filteredGroups.map((group) => (
              <div key={group.UUID} className="group-item">
                <div className="group-info">
                  {editingGroup === group.UUID ? (
                    <div className="group-edit-row">
                      <input
                        className="groups-input"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        onKeyDown={(e) =>
                          e.key === "Enter" && handleUpdate(group.UUID)
                        }
                        autoFocus
                      />
                      <button
                        className="btn-primary"
                        onClick={() => handleUpdate(group.UUID)}
                      >
                        {text.save}
                      </button>
                      <button
                        className="btn-ghost"
                        onClick={() => setEditingGroup(null)}
                      >
                        {text.cancel}
                      </button>
                    </div>
                  ) : (
                    <>
                      <strong className="group-name">{group.name}</strong>
                      <span className="group-meta">
                        {text.members}: {getGroupMemberCount(group)} &bull;{" "}
                        {text.meetings}: {group.meetings?.length ?? 0}
                      </span>
                    </>
                  )}
                </div>
                <div className="group-actions">
                  <button
                    className="btn-manage"
                    onClick={() => openModal(group)}
                  >
                    {text.manage}
                  </button>
                  {isAdmin && editingGroup !== group.UUID && (
                    <button
                      className="btn-ghost edit-soft-button"
                      onClick={() => {
                        setEditingGroup(group.UUID);
                        setEditName(group.name);
                      }}
                    >
                      {text.editName}
                    </button>
                  )}
                  {isAdmin && (
                    <button
                      className="btn-danger"
                      onClick={() => handleDelete(group)}
                    >
                      {text.delete}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Modal ניהול קבוצה */}
      {selectedGroup && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="groups-modal" onClick={(e) => e.stopPropagation()}>
            <div className="groups-modal-header">
              <h3>
                {text.manageTitle}: {selectedGroup.name}
              </h3>
              <button className="btn-ghost modal-close" onClick={closeModal}>
                ✕
              </button>
            </div>

            {modalLoading ? (
              <div className="groups-empty">{text.loading}</div>
            ) : (
              <div className="groups-modal-body">
                {modalError && <div className="groups-error">{modalError}</div>}
                <GroupMembersPanel
                  language={language}
                  selectedGroup={selectedGroup}
                  setSelectedGroup={setSelectedGroup}
                  modalMembers={modalMembers}
                  setModalMembers={setModalMembers}
                  allUsers={allUsers}
                  setAllUsers={setAllUsers}
                  setModalError={setModalError}
                  fetchGroups={fetchGroups}
                  currentUser={currentUser}
                />
                {isAdmin && (
                  <GroupMeetingsPanel
                    language={language}
                    selectedGroup={selectedGroup}
                    setSelectedGroup={setSelectedGroup}
                    allMeetings={allMeetings}
                    setAllMeetings={setAllMeetings}
                    groups={groups}
                    setGroups={setGroups}
                    setModalError={setModalError}
                    currentUser={currentUser}
                  />
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* modal אישור מחיקת קבוצה */}
      {showDeleteGroupConfirm && groupToDelete ? (
        <div className="modal-overlay" onClick={closeDeleteGroupConfirm}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">{text.deleteGroupModalTitle}</h3>
            <p
              style={{
                marginBottom: "20px",
                color: "#d32f2f",
                fontWeight: "500",
              }}
            >
              {text.deleteGroupModalMessage} "{groupToDelete.name}"?
            </p>

            <div className="modal-actions">
              <button
                className="btn-secondary"
                type="button"
                onClick={closeDeleteGroupConfirm}
                disabled={deleteGroupLoading}
              >
                {text.cancel}
              </button>
              <button
                className="btn-danger"
                type="button"
                onClick={confirmDeleteGroup}
                disabled={deleteGroupLoading}
              >
                {deleteGroupLoading ? text.deletingGroup : text.delete}
              </button>
            </div>
          </div>
        </div>
      ) : null}

    </div>
  );
}
