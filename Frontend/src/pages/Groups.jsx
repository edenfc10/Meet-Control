// Groups Page - ניהול קבוצות
// תומך ב: יצירה, מחיקה, עריכת שם, ניהול חברים + access_level, שיוך פגישות

import { useEffect, useMemo, useState } from "react";
import { groupAPI, userAPI, meetingAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Groups.css";

const ACCESS_LEVELS = ["audio", "video", "blast_dial"];

// היררכיית roles: super_admin > admin > agent > viewer
const ROLE_HIERARCHY = { super_admin: 4, admin: 3, agent: 2, viewer: 1 };

export default function Groups({ language = "en" }) {
  const { currentUser } = useAuth();
  const isHebrew = language === "he";
  const role = currentUser?.role;
  const myUUID = currentUser?.UUID || currentUser?.uuid;
  const myLevel = ROLE_HIERARCHY[role] || 0;
  const isAdmin = role === "admin" || role === "super_admin";
  const isAgent = role === "agent";
  const canReadAllUsers = role !== "viewer";
  // viewer לא יכול לנהל חברים בכלל
  const canManageMembers = myLevel >= 2;

  const accessLevelLabels = {
    audio: isHebrew ? "ועידות אודיו" : "audio",
    video: isHebrew ? "ועידות וידאו" : "video",
    blast_dial: isHebrew ? "ועידות הזנקה" : "blast_dial",
  };

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
    selectMeetingType: isHebrew
      ? "יש לבחור לפחות סוג ועידה אחד."
      : "Select at least one meeting type.",
    userAlreadyHasTypes: isHebrew
      ? "למשתמש כבר יש את כל סוגי הוועידות שנבחרו."
      : "Selected user already has all selected meeting types.",
    cannotAddSelf: isHebrew
      ? "אי אפשר להוסיף את עצמך לקבוצה."
      : "You cannot add yourself to a group.",
    addMemberError: isHebrew ? "הוספת המשתמש נכשלה." : "Failed to add member.",
    cannotRemoveSelf: isHebrew
      ? "אי אפשר להסיר את עצמך מהקבוצה."
      : "You cannot remove yourself from a group.",
    removeMemberError: isHebrew
      ? "הסרת המשתמש נכשלה."
      : "Failed to remove member.",
    cannotRemoveOwnAccess: isHebrew
      ? "אי אפשר להסיר לעצמך הרשאה מהקבוצה."
      : "You cannot remove your own access from a group.",
    removeMeetingTypeError: isHebrew
      ? "הסרת סוג הוועידה נכשלה."
      : "Failed to remove meeting type.",
    meetingAssignedElsewhere: isHebrew
      ? "הוועידה כבר משויכת לקבוצה אחרת ואי אפשר לצרף אותה לכאן."
      : "This meeting is already assigned to another group and cannot be added here.",
    meetingUnavailable: isHebrew
      ? "הוועידה הזאת לא זמינה לקבוצה הזו."
      : "This meeting is not available for this group.",
    addMeetingError: isHebrew
      ? "הוספת הוועידה נכשלה."
      : "Failed to add meeting.",
    removeMeetingError: isHebrew
      ? "הסרת הוועידה נכשלה."
      : "Failed to remove meeting.",
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
    viewersOnly: isHebrew ? " (צפיינים בלבד)" : " (Viewers only)",
    agentViewerOnly: isHebrew ? " (Agent ו-Viewer בלבד)" : " (Agent & Viewer)",
    noUsersToAdd: isHebrew
      ? "אין משתמשים זמינים להוספה."
      : "No users available to add.",
    searchUserPlaceholder: isHebrew
      ? "חיפוש משתמש ברשימה..."
      : "Search user in list...",
    searchUsersAria: isHebrew ? "חיפוש משתמשים" : "Search users",
    addableUsersAria: isHebrew ? "משתמשים זמינים להוספה" : "Addable users",
    noMatchingUsers: isHebrew
      ? "לא נמצאו משתמשים מתאימים."
      : "No matching users.",
    meetingTypesAria: isHebrew ? "סוגי ועידה" : "Meeting types",
    alreadyAssignedTitle: isHebrew ? "כבר משויך" : "Already assigned",
    toggleMeetingType: isHebrew ? "החלף סוג ועידה" : "Toggle meeting type",
    alreadyAssigned: isHebrew ? "כבר משויך" : "Already assigned",
    removeType: isHebrew ? "הסר סוג" : "Remove type",
    adding: isHebrew ? "מוסיף..." : "Adding...",
    add: isHebrew ? "הוסף" : "Add",
    meetingNumber: isHebrew ? "מספר ועידה" : "Meeting #",
    type: isHebrew ? "סוג" : "Type",
    remove: isHebrew ? "הסר" : "Remove",
    searchMeetingPlaceholder: isHebrew
      ? "חיפוש ועידה לפי מספר או סוג..."
      : "Search meeting by number or type...",
    selectFromResults: isHebrew ? "בחר מתוך התוצאות" : "Select from results",
    noMatchingMeetings: isHebrew
      ? "לא נמצאו ועידות מתאימות."
      : "No matching meetings.",
    noMeetingsToAdd: isHebrew
      ? "אין ועידות זמינות להוספה."
      : "No meetings available to add.",
  };

  const formatAccessLevel = (level) => accessLevelLabels[level] || level;

  // קבוצות
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // חיפוש
  const [search, setSearch] = useState("");
  const [accessFilter, setAccessFilter] = useState("all");

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
  const [showRemoveMemberConfirm, setShowRemoveMemberConfirm] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState(null);
  const [removeMemberLoadingId, setRemoveMemberLoadingId] = useState("");

  // הוספת חבר
  const [allUsers, setAllUsers] = useState([]);
  const [addUserId, setAddUserId] = useState("");
  const [addAccessLevels, setAddAccessLevels] = useState([]);
  const [addMemberLoading, setAddMemberLoading] = useState(false);

  // שיוך פגישה
  const [allMeetings, setAllMeetings] = useState([]);
  const [addMeetingId, setAddMeetingId] = useState("");
  const [addMeetingLoading, setAddMeetingLoading] = useState(false);
  const [removeMeetingId, setRemoveMeetingId] = useState(null);
  const [removeMeetingLoading, setRemoveMeetingLoading] = useState(false);

  // חיפוש משתמשים ומיטינגים
  const [searchUserText, setSearchUserText] = useState("");
  const [searchMeetingText, setSearchMeetingText] = useState("");

  const getUserAccessLevelsInSelectedGroup = (userId) => {
    if (!userId) return [];
    const rows = selectedGroup?.member_access_levels || [];
    return Array.from(
      new Set(
        rows
          .filter((row) => String(row.user_id) === String(userId))
          .map((row) => row.access_level),
      ),
    );
  };

  const getMemberAccessLevels = (memberUuid) => {
    const rows = selectedGroup?.member_access_levels || [];
    return Array.from(
      new Set(
        rows
          .filter((row) => String(row.user_id) === String(memberUuid))
          .map((row) => row.access_level),
      ),
    );
  };

  const getGroupMemberCount = (group) => {
    const memberIds = (group?.members || []).map((member) => String(member));

    if (memberIds.length > 0) {
      return new Set(memberIds).size;
    }

    const accessRows = group?.member_access_levels || [];
    return new Set(accessRows.map((row) => String(row.user_id))).size;
  };

  const addableUsers = useMemo(() => {
    return (allUsers || []).filter((u) => {
      const uLevel = ROLE_HIERARCHY[u.role] || 0;
      if (u.UUID === myUUID || uLevel >= myLevel) {
        return false;
      }
      const existingLevels = getUserAccessLevelsInSelectedGroup(u.UUID);
      return existingLevels.length < ACCESS_LEVELS.length;
    });
  }, [allUsers, myUUID, myLevel, selectedGroup?.member_access_levels]);

  const filteredAddableUsers = useMemo(() => {
    const q = searchUserText.trim().toLowerCase();
    if (!q) return addableUsers;
    return addableUsers.filter(
      (u) =>
        (u.username || "").toLowerCase().startsWith(q) ||
        (u.s_id || "").toLowerCase().startsWith(q) ,
    );
  }, [addableUsers, searchUserText]);

  const existingAccessLevelsForSelectedUser = useMemo(() => {
    if (!addUserId) return [];
    return getUserAccessLevelsInSelectedGroup(addUserId);
  }, [addUserId, selectedGroup?.member_access_levels]);

  const selectedAddUser = useMemo(() => {
    if (!addUserId) return null;
    return (
      (allUsers || []).find((u) => String(u.UUID) === String(addUserId)) || null
    );
  }, [addUserId, allUsers]);

  const canRemoveAccessFromSelectedUser =
    isAdmin || (isAgent && selectedAddUser?.role === "viewer");

  const newAccessLevelsToAdd = useMemo(() => {
    return addAccessLevels.filter(
      (level) => !existingAccessLevelsForSelectedUser.includes(level),
    );
  }, [addAccessLevels, existingAccessLevelsForSelectedUser]);

  const selectedGroupMeetingIds = useMemo(() => {
    return new Set((selectedGroup?.meetings || []).map((id) => String(id)));
  }, [selectedGroup?.meetings]);

  const meetingsAssignedToOtherGroups = useMemo(() => {
    const assigned = new Set();
    (groups || []).forEach((group) => {
      if (String(group?.UUID) === String(selectedGroup?.UUID)) {
        return;
      }
      (group?.meetings || []).forEach((meetingId) => {
        assigned.add(String(meetingId));
      });
    });
    return assigned;
  }, [groups, selectedGroup?.UUID]);

  const addableMeetingsForSelectedGroup = useMemo(() => {
    return (allMeetings || []).filter((meeting) => {
      const meetingId = String(meeting.UUID);
      if (selectedGroupMeetingIds.has(meetingId)) {
        return false;
      }
      return !meetingsAssignedToOtherGroups.has(meetingId);
    });
  }, [allMeetings, selectedGroupMeetingIds, meetingsAssignedToOtherGroups]);

  const filteredAddableMeetings = useMemo(() => {
    const q = searchMeetingText.trim().toLowerCase();
    if (!q) return addableMeetingsForSelectedGroup;
    return addableMeetingsForSelectedGroup.filter(
      (m) =>
        String(m.m_number).startsWith(q) ||
        (m.accessLevel || "").toLowerCase().startsWith(q),
    );
  }, [addableMeetingsForSelectedGroup, searchMeetingText]);

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
    setAddUserId("");
    setAddMeetingId("");
    setAddAccessLevels([]);
    try {
      const [membersResp, usersResp, meetingsResp] = await Promise.allSettled([
        groupAPI.getGroupMembers(group.UUID),
        canReadAllUsers ? userAPI.getAllUsers() : Promise.resolve({ data: [] }),
        meetingAPI.getAllMeetings(),
      ]);
      const members =
        membersResp.status === "fulfilled" ? membersResp.value.data || [] : [];
      setModalMembers(members);
      const users =
        usersResp.status === "fulfilled" ? usersResp.value.data || [] : [];
      setAllUsers(users);
      const meetings =
        meetingsResp.status === "fulfilled"
          ? meetingsResp.value.data || []
          : [];
      setAllMeetings(meetings);
      const firstError = [membersResp, usersResp, meetingsResp].find(
        (r) => r.status === "rejected",
      );
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
    setSearchUserText("");
    setSearchMeetingText("");
  };

  useEffect(() => {
    if (!addUserId) {
      setAddAccessLevels([]);
      return;
    }

    setAddAccessLevels([]);
  }, [addUserId, selectedGroup?.member_access_levels]);

  useEffect(() => {
    if (!addMeetingId) return;
    const stillAvailable = addableMeetingsForSelectedGroup.some(
      (meeting) => String(meeting.UUID) === String(addMeetingId),
    );
    if (!stillAvailable) {
      setAddMeetingId("");
    }
  }, [addMeetingId, addableMeetingsForSelectedGroup]);

  // --- הוספת חבר ---
  const handleAddMember = async () => {
    if (!addUserId || !selectedGroup) return;
    if (addAccessLevels.length === 0) {
      setModalError(text.selectMeetingType);
      return;
    }
    if (newAccessLevelsToAdd.length === 0) {
      setModalError(text.userAlreadyHasTypes);
      return;
    }
    // מניעת שיוך עצמי לקבוצה
    if (addUserId === currentUser?.UUID) {
      setModalError(text.cannotAddSelf);
      return;
    }
    setAddMemberLoading(true);
    setModalError("");
    try {
      const responses = await Promise.all(
        newAccessLevelsToAdd.map((level) =>
          groupAPI.addMember(selectedGroup.UUID, addUserId, level),
        ),
      );
      // רענון חברים ורשימת משתמשים
      const [membersResp, usersResp] = await Promise.all([
        groupAPI.getGroupMembers(selectedGroup.UUID),
        canReadAllUsers ? userAPI.getAllUsers() : Promise.resolve({ data: [] }),
      ]);
      const members = membersResp.data || [];
      setModalMembers(members);
      setAllUsers(usersResp.data || []);
      const latestGroup = responses[responses.length - 1]?.data;
      if (latestGroup) {
        setSelectedGroup(latestGroup);
      }
      setAddUserId("");
      setAddAccessLevels([]);
      await fetchGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || text.addMemberError);
    } finally {
      setAddMemberLoading(false);
    }
  };

  // --- הסרת חבר ---
  const handleRemoveMember = (userId, username) => {
    if (!selectedGroup) return;
    // מניעת הסרה עצמית מקבוצה
    if (userId === currentUser?.UUID) {
      setModalError(text.cannotRemoveSelf);
      return;
    }

    setMemberToRemove({ userId, username });
    setShowRemoveMemberConfirm(true);
  };

  const closeRemoveMemberConfirm = () => {
    if (removeMemberLoadingId) return;
    setShowRemoveMemberConfirm(false);
    setMemberToRemove(null);
  };

  const confirmRemoveMember = async () => {
    if (!selectedGroup || !memberToRemove?.userId) return;

    const userId = memberToRemove.userId;
    setRemoveMemberLoadingId(String(userId));
    setModalError("");
    try {
      await groupAPI.removeMember(selectedGroup.UUID, userId);
      const [membersResp, usersResp] = await Promise.all([
        groupAPI.getGroupMembers(selectedGroup.UUID),
        canReadAllUsers ? userAPI.getAllUsers() : Promise.resolve({ data: [] }),
      ]);
      const members = membersResp.data || [];
      setModalMembers(members);
      setAllUsers(usersResp.data || []);
      closeRemoveMemberConfirm();
      await fetchGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || text.removeMemberError);
    } finally {
      setRemoveMemberLoadingId("");
    }
  };

  const handleRemoveMemberAccess = async (userId, accessLevel) => {
    if (!selectedGroup) return;
    if (userId === currentUser?.UUID) {
      setModalError(text.cannotRemoveOwnAccess);
      return;
    }
    setModalError("");
    try {
      await groupAPI.removeMemberAccess(
        selectedGroup.UUID,
        userId,
        accessLevel,
      );
      const [membersResp, usersResp] = await Promise.all([
        groupAPI.getGroupMembers(selectedGroup.UUID),
        canReadAllUsers ? userAPI.getAllUsers() : Promise.resolve({ data: [] }),
      ]);
      const members = membersResp.data || [];
      setModalMembers(members);
      setAllUsers(usersResp.data || []);
      const groupResp = await groupAPI.getGroup(selectedGroup.UUID);
      setSelectedGroup(groupResp.data);
      await fetchGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || text.removeMeetingTypeError);
    }
  };

  // --- שיוך פגישה לקבוצה ---
  const handleAddMeeting = async () => {
    if (!addMeetingId || !selectedGroup) return;

    if (meetingsAssignedToOtherGroups.has(String(addMeetingId))) {
      setModalError(text.meetingAssignedElsewhere);
      return;
    }

    const canAddMeeting = addableMeetingsForSelectedGroup.some(
      (meeting) => String(meeting.UUID) === String(addMeetingId),
    );
    if (!canAddMeeting) {
      setModalError(text.meetingUnavailable);
      return;
    }

    setAddMeetingLoading(true);
    setModalError("");
    try {
      await groupAPI.addMeeting(selectedGroup.UUID, addMeetingId);
      setAddMeetingId("");
      const resp = await groupAPI.listGroups();
      const updated = (resp.data || []).find(
        (g) => g.UUID === selectedGroup.UUID,
      );
      if (updated) {
        setSelectedGroup(updated);
        setGroups(resp.data || []);
      }
    } catch (err) {
      setModalError(err.response?.data?.detail || text.addMeetingError);
    } finally {
      setAddMeetingLoading(false);
    }
  };

  // --- הסרת פגישה מקבוצה ---
  const handleRemoveMeeting = async (meetingUuid) => {
    if (!selectedGroup) return;
    setModalError("");
    try {
      await groupAPI.removeMeeting(selectedGroup.UUID, meetingUuid);
      const resp = await groupAPI.listGroups();
      const updated = (resp.data || []).find(
        (g) => g.UUID === selectedGroup.UUID,
      );
      if (updated) {
        setSelectedGroup(updated);
        setGroups(resp.data || []);
      }
    } catch (err) {
      setModalError(err.response?.data?.detail || text.removeMeetingError);
    }
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

                {/* חברים קיימים */}
                <div className="groups-modal-section">
                  <h4>
                    {text.currentMembers} ({modalMembers.length})
                  </h4>
                  {modalMembers.length === 0 ? (
                    <div className="groups-empty">{text.noMembers}</div>
                  ) : (
                    <table className="groups-table">
                      <thead>
                        <tr>
                          <th>S_ID</th>
                          <th>{text.username}</th>
                          <th>{text.tableRole}</th>
                          <th>{text.meetingTypes}</th>
                          {(isAdmin || isAgent) && <th></th>}
                        </tr>
                      </thead>
                      <tbody>
                        {modalMembers.map((member) => (
                          <tr key={member.s_id}>
                            <td>{member.s_id}</td>
                            <td>{member.username}</td>
                            <td>
                              <span
                                className={`role-badge role-${member.role}`}
                              >
                                {member.role}
                              </span>
                            </td>
                            <td>
                              <div className="member-access-list">
                                {getMemberAccessLevels(member.UUID).length >
                                0 ? (
                                  getMemberAccessLevels(member.UUID).map(
                                    (lvl) => {
                                      const canRemoveLevel =
                                        isAdmin ||
                                        (isAgent && member.role === "viewer");
                                      return (
                                        <span
                                          key={`${member.UUID}-${lvl}`}
                                          className="member-access-badge member-access-pill"
                                        >
                                          <span>{formatAccessLevel(lvl)}</span>
                                          {canRemoveLevel && (
                                            <button
                                              type="button"
                                              className="member-access-remove"
                                              onClick={() =>
                                                handleRemoveMemberAccess(
                                                  member.UUID || member.s_id,
                                                  lvl,
                                                )
                                              }
                                              title={`${text.remove} ${formatAccessLevel(lvl)}`}
                                            >
                                              ×
                                            </button>
                                          )}
                                        </span>
                                      );
                                    },
                                  )
                                ) : (
                                  <span className="groups-empty">
                                    {text.noAccessLevels}
                                  </span>
                                )}
                              </div>
                            </td>
                            {(isAdmin ||
                              (isAgent && member.role === "viewer")) && (
                              <td>
                                <button
                                  className="btn-danger btn-sm"
                                  onClick={() =>
                                    handleRemoveMember(
                                      member.UUID || member.s_id,
                                      member.username,
                                    )
                                  }
                                >
                                  {text.removeUser}
                                </button>
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>

                {/* הוספת חבר */}
                {canManageMembers && (
                  <div className="groups-modal-section">
                    <h4>
                      {text.addMember}
                      {role === "agent"
                        ? text.viewersOnly
                        : role === "admin"
                          ? text.agentViewerOnly
                          : ""}
                    </h4>
                    {addableUsers.length === 0 ? (
                      <div className="groups-empty">{text.noUsersToAdd}</div>
                    ) : (
                      <div className="groups-add-row groups-add-member-row">
                        <div className="groups-search-select" role="group">
                          <input
                            className="groups-search-select-input"
                            type="text"
                            placeholder={text.searchUserPlaceholder}
                            value={searchUserText}
                            onChange={(e) => setSearchUserText(e.target.value)}
                            aria-label={text.searchUsersAria}
                          />
                          <div
                            className="groups-search-select-list"
                            role="listbox"
                            aria-label={text.addableUsersAria}
                          >
                            {filteredAddableUsers.length > 0 ? (
                              filteredAddableUsers.map((u) => {
                                const selected =
                                  String(addUserId) === String(u.UUID);
                                return (
                                  <button
                                    key={u.UUID}
                                    type="button"
                                    role="option"
                                    aria-selected={selected}
                                    className={`groups-search-select-option ${selected ? "is-selected" : ""}`}
                                    onClick={() => setAddUserId(String(u.UUID))}
                                  >
                                    {u.username} ({u.s_id}) — {u.role}
                                  </button>
                                );
                              })
                            ) : (
                              <div
                                className="groups-empty"
                                style={{ padding: "8px" }}
                              >
                                {text.noMatchingUsers}
                              </div>
                            )}
                          </div>
                        </div>
                        {canManageMembers && (
                          <div className="groups-types-field">
                            <div className="groups-field-label">
                              TYPE MEETINGS
                            </div>
                            <div
                              className="groups-access-segmented"
                              role="group"
                              aria-label={text.meetingTypesAria}
                            >
                              {ACCESS_LEVELS.map((lvl) => {
                                const active = addAccessLevels.includes(lvl);
                                const isExisting =
                                  existingAccessLevelsForSelectedUser.includes(
                                    lvl,
                                  );
                                return (
                                  <button
                                    key={lvl}
                                    type="button"
                                    className={`groups-segment-btn ${active ? "is-active" : ""} ${isExisting ? "is-assigned" : ""}`}
                                    title={
                                      isExisting
                                        ? canRemoveAccessFromSelectedUser
                                          ? `${text.removeType} ${formatAccessLevel(lvl)}`
                                          : text.alreadyAssignedTitle
                                        : text.toggleMeetingType
                                    }
                                    onClick={() => {
                                      if (isExisting) {
                                        if (!canRemoveAccessFromSelectedUser)
                                          return;
                                        handleRemoveMemberAccess(
                                          addUserId,
                                          lvl,
                                        );
                                        return;
                                      }
                                      if (active) {
                                        setAddAccessLevels((prev) =>
                                          prev.filter((x) => x !== lvl),
                                        );
                                      } else {
                                        setAddAccessLevels((prev) =>
                                          prev.includes(lvl)
                                            ? prev
                                            : [...prev, lvl],
                                        );
                                      }
                                    }}
                                  >
                                    {formatAccessLevel(lvl)}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        )}
                        <button
                          className="btn-primary"
                          onClick={handleAddMember}
                          disabled={
                            addMemberLoading ||
                            !addUserId ||
                            addAccessLevels.length === 0 ||
                            newAccessLevelsToAdd.length === 0
                          }
                        >
                          {addMemberLoading ? text.adding : text.add}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* שיוך פגישה */}
                {isAdmin && (
                  <div className="groups-modal-section">
                    <h4>
                      {text.meetings} ({selectedGroup.meetings?.length ?? 0})
                    </h4>
                    {/* פגישות קיימות בקבוצה */}
                    {selectedGroup.meetings?.length > 0 && (
                      <table className="groups-table">
                        <thead>
                          <tr>
                            <th>{text.meetingNumber}</th>
                            <th>{text.type}</th>
                            <th></th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedGroup.meetings.map((mId) => {
                            const meeting = allMeetings.find(
                              (m) => m.UUID === mId || m.UUID === String(mId),
                            );
                            return (
                              <tr key={mId}>
                                <td>
                                  {meeting
                                    ? `#${meeting.m_number}`
                                    : String(mId).slice(0, 8) + "..."}
                                </td>
                                <td>
                                  {meeting
                                    ? formatAccessLevel(meeting.accessLevel)
                                    : "—"}
                                </td>
                                <td>
                                  <button
                                    className="btn-danger btn-sm"
                                    onClick={() =>
                                      handleRemoveMeeting(String(mId))
                                    }
                                  >
                                    {text.remove}
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    )}
                    {/* הוספת פגישה */}
                    {addableMeetingsForSelectedGroup.length === 0 ? (
                      <div className="groups-empty">{text.noMeetingsToAdd}</div>
                    ) : (
                      <div className="groups-add-row groups-add-meeting-row">
                        <div className="groups-search-select" role="group">
                          <input
                            className="groups-search-select-input"
                            type="text"
                            placeholder={text.searchMeetingPlaceholder}
                            value={searchMeetingText}
                            onChange={(e) => setSearchMeetingText(e.target.value)}
                            aria-label="Search meetings"
                          />
                          <div
                            className="groups-search-select-list"
                            role="listbox"
                            aria-label="Available meetings"
                          >
                            {filteredAddableMeetings.length > 0 ? (
                              filteredAddableMeetings.map((m) => {
                                const selected =
                                  String(addMeetingId) === String(m.UUID);
                                return (
                                  <button
                                    key={m.UUID}
                                    type="button"
                                    role="option"
                                    aria-selected={selected}
                                    className={`groups-search-select-option ${selected ? "is-selected" : ""}`}
                                    onClick={() => {
                                      setAddMeetingId(m.UUID);
                                      setSearchMeetingText("");
                                    }}
                                  >
                                    #{m.m_number} ({formatAccessLevel(m.accessLevel)})
                                  </button>
                                );
                              })
                            ) : (
                              <div
                                className="groups-empty"
                                style={{ padding: "8px" }}
                              >
                                {searchMeetingText
                                  ? text.noMatchingMeetings
                                  : ""}
                              </div>
                            )}
                          </div>
                        </div>
                        <button
                          className="btn-primary"
                          onClick={handleAddMeeting}
                          disabled={
                            addMeetingLoading ||
                            !addMeetingId ||
                            addableMeetingsForSelectedGroup.length === 0
                          }
                        >
                          {addMeetingLoading ? text.adding : text.add}
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

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

      {showRemoveMemberConfirm && memberToRemove ? (
        <div className="modal-overlay" onClick={closeRemoveMemberConfirm}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">{text.removeMemberModalTitle}</h3>
            <p
              style={{
                marginBottom: "20px",
                color: "#d32f2f",
                fontWeight: "500",
              }}
            >
              {text.removeMemberModalMessage} "{memberToRemove.username}"?
            </p>

            <div className="modal-actions">
              <button
                className="btn-secondary"
                type="button"
                onClick={closeRemoveMemberConfirm}
                disabled={
                  removeMemberLoadingId === String(memberToRemove.userId)
                }
              >
                {text.cancel}
              </button>
              <button
                className="btn-danger"
                type="button"
                onClick={confirmRemoveMember}
                disabled={
                  removeMemberLoadingId === String(memberToRemove.userId)
                }
              >
                {removeMemberLoadingId === String(memberToRemove.userId)
                  ? text.removingUser
                  : text.removeUser}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
