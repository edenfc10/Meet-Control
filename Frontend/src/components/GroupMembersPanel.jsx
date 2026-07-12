import { useMemo, useState, useEffect } from "react";
import { groupAPI, userAPI } from "../services/api";

const ACCESS_LEVELS = ["audio", "video", "blast_dial"];
const ROLE_HIERARCHY = { super_admin: 4, admin: 3, agent: 2 };

export default function GroupMembersPanel({
  language,
  selectedGroup,
  setSelectedGroup,
  modalMembers,
  setModalMembers,
  allUsers,
  setAllUsers,
  setModalError,
  fetchGroups,
  currentUser,
}) {
  const isHebrew = language === "he";
  const role = currentUser?.role;
  const myUUID = currentUser?.UUID || currentUser?.uuid;
  const myLevel = ROLE_HIERARCHY[role] || 0;
  const isAdmin = role === "admin" || role === "super_admin";
  const isAgent = role === "agent";
  const canReadAllUsers = myLevel >= 2;
  const canManageMembers = myLevel >= 2;

  const availableAccessLevels = ACCESS_LEVELS;

  const accessLevelLabels = {
    audio: isHebrew ? "ועידות אודיו" : "audio",
    video: isHebrew ? "ועידות וידאו" : "video",
    blast_dial: isHebrew ? "ועידות הזנקה" : "blast_dial",
  };
  const formatAccessLevel = (level) => accessLevelLabels[level] || level;

  const text = {
    currentMembers: isHebrew ? "חברים נוכחיים" : "Current Members",
    noMembers: isHebrew ? "עדיין אין חברים." : "No members yet.",
    username: isHebrew ? "שם משתמש" : "Username",
    tableRole: isHebrew ? "תפקיד" : "Role",
    meetingTypes: isHebrew ? "סוגי ועידה" : "Meeting Types",
    noAccessLevels: isHebrew ? "אין הרשאות" : "No access levels",
    removeUser: isHebrew ? "הסר משתמש" : "Remove User",
    removeMemberModalTitle: isHebrew ? "הסרת שיוך משתמש מהמדור" : "Remove User Assignment",
    removeMemberModalMessage: isHebrew ? "האם אתה בטוח שברצונך להסיר את המשתמש" : "Are you sure you want to remove user",
    removingUser: isHebrew ? "מסיר..." : "Removing...",
    addMember: isHebrew ? "הוספת חבר" : "Add Member",
    agentsOnly: isHebrew ? " (Agents בלבד)" : " (Agents only)",
    agentOnly: isHebrew ? " (Agent בלבד)" : " (Agents only)",
    noUsersToAdd: isHebrew ? "אין משתמשים זמינים להוספה." : "No users available to add.",
    searchUsersAria: isHebrew ? "חיפוש משתמשים" : "Search users",
    addableUsersAria: isHebrew ? "משתמשים זמינים להוספה" : "Addable users",
    noMatchingUsers: isHebrew ? "לא נמצאו משתמשים מתאימים." : "No matching users.",
    meetingTypesAria: isHebrew ? "סוגי ועידה" : "Meeting types",
    alreadyAssignedTitle: isHebrew ? "כבר משויך" : "Already assigned",
    toggleMeetingType: isHebrew ? "החלף סוג ועידה" : "Toggle meeting type",
    removeType: isHebrew ? "הסר סוג" : "Remove type",
    adding: isHebrew ? "מוסיף..." : "Adding...",
    add: isHebrew ? "הוסף" : "Add",
    cancel: isHebrew ? "ביטול" : "Cancel",
    remove: isHebrew ? "הסר" : "Remove",
    selectMeetingType: isHebrew ? "יש לבחור לפחות סוג ועידה אחד." : "Select at least one meeting type.",
    userAlreadyHasTypes: isHebrew ? "למשתמש כבר יש את כל סוגי הוועידות שנבחרו." : "Selected user already has all selected meeting types.",
    cannotAddSelf: isHebrew ? "אי אפשר להוסיף את עצמך לקבוצה." : "You cannot add yourself to a group.",
    addMemberError: isHebrew ? "הוספת המשתמש נכשלה." : "Failed to add member.",
    cannotRemoveSelf: isHebrew ? "אי אפשר להסיר את עצמך מהקבוצה." : "You cannot remove yourself from a group.",
    removeMemberError: isHebrew ? "הסרת המשתמש נכשלה." : "Failed to remove member.",
    cannotRemoveOwnAccess: isHebrew ? "אי אפשר להסיר לעצמך הרשאה מהקבוצה." : "You cannot remove your own access from a group.",
    removeMeetingTypeError: isHebrew ? "הסרת סוג הוועידה נכשלה." : "Failed to remove meeting type.",
  };

  const [addUserId, setAddUserId] = useState("");
  const [addAccessLevels, setAddAccessLevels] = useState([]);
  const [addMemberLoading, setAddMemberLoading] = useState(false);
  const [searchUserText, setSearchUserText] = useState("");
  const [showRemoveMemberConfirm, setShowRemoveMemberConfirm] = useState(false);
  const [memberToRemove, setMemberToRemove] = useState(null);
  const [removeMemberLoadingId, setRemoveMemberLoadingId] = useState("");

  useEffect(() => {
    setAddUserId("");
    setAddAccessLevels([]);
    setSearchUserText("");
  }, [selectedGroup?.UUID]);

  useEffect(() => {
    setAddAccessLevels([]);
  }, [addUserId]);

  const getUserAccessLevelsInSelectedGroup = (userId) => {
    if (!userId) return [];
    const rows = selectedGroup?.member_access_levels || [];
    return Array.from(new Set(rows.filter((r) => String(r.user_id) === String(userId)).map((r) => r.access_level)));
  };

  const getMemberAccessLevels = (memberUuid) => {
    const rows = selectedGroup?.member_access_levels || [];
    return Array.from(new Set(rows.filter((r) => String(r.user_id) === String(memberUuid)).map((r) => r.access_level)));
  };

  const addableUsers = useMemo(() => {
    return (allUsers || []).filter((u) => {
      if (u.role !== "agent") return false;
      if (u.UUID === myUUID) return false;
      const existingLevels = getUserAccessLevelsInSelectedGroup(u.UUID);
      return existingLevels.length < availableAccessLevels.length;
    });
  }, [allUsers, myUUID, selectedGroup?.member_access_levels]);

  const filteredAddableUsers = useMemo(() => {
    const q = searchUserText.trim().toLowerCase();
    if (!q) return addableUsers;
    return addableUsers.filter(
      (u) => (u.username || "").toLowerCase().includes(q) || (u.s_id || "").toLowerCase().includes(q)
    );
  }, [addableUsers, searchUserText]);

  const existingAccessLevelsForSelectedUser = useMemo(() => {
    if (!addUserId) return [];
    return getUserAccessLevelsInSelectedGroup(addUserId);
  }, [addUserId, selectedGroup?.member_access_levels]);

  const selectedAddUser = useMemo(() => {
    if (!addUserId) return null;
    return (allUsers || []).find((u) => String(u.UUID) === String(addUserId)) || null;
  }, [addUserId, allUsers]);

  const canRemoveAccessFromSelectedUser = isAdmin || (isAgent && selectedAddUser?.role === "agent");

  const newAccessLevelsToAdd = useMemo(() => {
    return addAccessLevels.filter((level) => !existingAccessLevelsForSelectedUser.includes(level));
  }, [addAccessLevels, existingAccessLevelsForSelectedUser]);

  const refreshMembers = async () => {
    const [membersResp, usersResp] = await Promise.all([
      groupAPI.getGroupMembers(selectedGroup.UUID),
      canReadAllUsers ? userAPI.getAllUsers() : Promise.resolve({ data: [] }),
    ]);
    setModalMembers(membersResp.data || []);
    setAllUsers(usersResp.data || []);
  };

  const handleAddMember = async () => {
    if (!addUserId || !selectedGroup) return;
    if (addAccessLevels.length === 0) { setModalError(text.selectMeetingType); return; }
    if (newAccessLevelsToAdd.length === 0) { setModalError(text.userAlreadyHasTypes); return; }
    if (addUserId === myUUID) { setModalError(text.cannotAddSelf); return; }
    setAddMemberLoading(true);
    setModalError("");
    try {
      const responses = await Promise.all(
        newAccessLevelsToAdd.map((level) => groupAPI.addMember(selectedGroup.UUID, addUserId, level))
      );
      await refreshMembers();
      const latestGroup = responses[responses.length - 1]?.data;
      if (latestGroup) setSelectedGroup(latestGroup);
      setAddUserId("");
      setAddAccessLevels([]);
      await fetchGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || text.addMemberError);
    } finally {
      setAddMemberLoading(false);
    }
  };

  const handleRemoveMember = (userId, username) => {
    if (!selectedGroup) return;
    if (userId === myUUID) { setModalError(text.cannotRemoveSelf); return; }
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
      await refreshMembers();
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
    if (userId === myUUID) { setModalError(text.cannotRemoveOwnAccess); return; }
    setModalError("");
    try {
      await groupAPI.removeMemberAccess(selectedGroup.UUID, userId, accessLevel);
      await refreshMembers();
      const groupResp = await groupAPI.getGroup(selectedGroup.UUID);
      setSelectedGroup(groupResp.data);
      await fetchGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || text.removeMeetingTypeError);
    }
  };

  return (
    <>
      {/* חברים קיימים */}
      <div className="groups-modal-section">
        <h4>{text.currentMembers} ({modalMembers.length})</h4>
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
                    <span className={`role-badge role-${member.role}`}>{member.role}</span>
                  </td>
                  <td>
                    <div className="member-access-list">
                      {getMemberAccessLevels(member.UUID).length > 0 ? (
                        getMemberAccessLevels(member.UUID).map((lvl) => {
                          const canRemoveLevel =
                            (isAdmin && availableAccessLevels.includes(lvl)) ||
                            (isAgent && member.role === "agent");
                          return (
                            <span key={`${member.UUID}-${lvl}`} className="member-access-badge member-access-pill">
                              <span>{formatAccessLevel(lvl)}</span>
                              {canRemoveLevel && (
                                <button
                                  type="button"
                                  className="member-access-remove"
                                  onClick={() => handleRemoveMemberAccess(member.UUID || member.s_id, lvl)}
                                  title={`${text.remove} ${formatAccessLevel(lvl)}`}
                                >
                                  ×
                                </button>
                              )}
                            </span>
                          );
                        })
                      ) : (
                        <span className="groups-empty">{text.noAccessLevels}</span>
                      )}
                    </div>
                  </td>
                  {(isAdmin || (isAgent && member.role === "agent")) && (
                    <td>
                      <button
                        className="btn-danger btn-sm"
                        onClick={() => handleRemoveMember(member.UUID || member.s_id, member.username)}
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
            {role === "agent" ? text.agentsOnly : role === "admin" ? text.agentOnly : ""}
          </h4>
          {addableUsers.length === 0 ? (
            <div className="groups-empty">{text.noUsersToAdd}</div>
          ) : (
            <div className="groups-add-row groups-add-member-row">
              <div className="groups-search-select" role="group">
                <input
                  className="groups-search-select-input"
                  type="text"
                  placeholder={isHebrew ? "חיפוש לפי שם משתמש או ID..." : "Search by username or ID..."}
                  value={searchUserText}
                  onChange={(e) => setSearchUserText(e.target.value)}
                  aria-label={text.searchUsersAria}
                />
                <div className="groups-search-select-list" role="listbox" aria-label={text.addableUsersAria}>
                  {filteredAddableUsers.length > 0 ? (
                    filteredAddableUsers.map((u) => {
                      const selected = String(addUserId) === String(u.UUID);
                      return (
                        <button
                          key={u.UUID}
                          type="button"
                          role="option"
                          aria-selected={selected}
                          className={`groups-search-select-option ${selected ? "is-selected" : ""}`}
                          onClick={() => { setAddUserId(String(u.UUID)); setSearchUserText(""); }}
                        >
                          <span>{u.username}</span>
                          <span style={{ color: "#888", fontSize: "0.82em", marginLeft: 4 }}>{u.s_id}</span>
                          <span className={`role-badge role-${u.role}`} style={{ marginLeft: 6, fontSize: "0.78em" }}>{u.role}</span>
                        </button>
                      );
                    })
                  ) : (
                    <div className="groups-empty" style={{ padding: "8px" }}>{text.noMatchingUsers}</div>
                  )}
                </div>
              </div>
              <div className="groups-types-field">
                <div className="groups-field-label">{text.meetingTypes}</div>
                {selectedAddUser && (
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 6, padding: "4px 8px", background: "#f0f4ff", borderRadius: 6, fontSize: "0.85em", border: "1px solid #c5d0f5" }}>
                    <span style={{ fontWeight: 600 }}>{selectedAddUser.username}</span>
                    <span style={{ color: "#888" }}>({selectedAddUser.s_id})</span>
                    <span className={`role-badge role-${selectedAddUser.role}`} style={{ fontSize: "0.78em" }}>{selectedAddUser.role}</span>
                    <button type="button" onClick={() => setAddUserId("")} style={{ marginLeft: "auto", background: "none", border: "none", cursor: "pointer", color: "#888", fontSize: "1em", lineHeight: 1 }}>✕</button>
                  </div>
                )}
                <div className="groups-access-segmented" role="group" aria-label={text.meetingTypesAria}>
                  {availableAccessLevels.map((lvl) => {
                    const active = addAccessLevels.includes(lvl);
                    const isExisting = existingAccessLevelsForSelectedUser.includes(lvl);
                    return (
                      <button
                        key={lvl}
                        type="button"
                        className={`groups-segment-btn ${active ? "is-active" : ""} ${isExisting ? "is-assigned" : ""}`}
                        title={isExisting ? (canRemoveAccessFromSelectedUser ? `${text.removeType} ${formatAccessLevel(lvl)}` : text.alreadyAssignedTitle) : text.toggleMeetingType}
                        onClick={() => {
                          if (isExisting) {
                            if (!canRemoveAccessFromSelectedUser) return;
                            handleRemoveMemberAccess(addUserId, lvl);
                            return;
                          }
                          if (active) {
                            setAddAccessLevels((prev) => prev.filter((x) => x !== lvl));
                          } else {
                            setAddAccessLevels((prev) => prev.includes(lvl) ? prev : [...prev, lvl]);
                          }
                        }}
                      >
                        {formatAccessLevel(lvl)}
                      </button>
                    );
                  })}
                </div>
              </div>
              <button
                className="btn-primary"
                onClick={handleAddMember}
                disabled={addMemberLoading || !addUserId || addAccessLevels.length === 0 || newAccessLevelsToAdd.length === 0}
              >
                {addMemberLoading ? text.adding : text.add}
              </button>
            </div>
          )}
        </div>
      )}

      {/* modal אישור הסרת חבר */}
      {showRemoveMemberConfirm && memberToRemove && (
        <div className="modal-overlay" onClick={closeRemoveMemberConfirm}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">{text.removeMemberModalTitle}</h3>
            <p style={{ marginBottom: "20px", color: "#d32f2f", fontWeight: "500" }}>
              {text.removeMemberModalMessage} "{memberToRemove.username}"?
            </p>
            <div className="modal-actions">
              <button
                className="btn-secondary"
                type="button"
                onClick={closeRemoveMemberConfirm}
                disabled={removeMemberLoadingId === String(memberToRemove.userId)}
              >
                {text.cancel}
              </button>
              <button
                className="btn-danger"
                type="button"
                onClick={confirmRemoveMember}
                disabled={removeMemberLoadingId === String(memberToRemove.userId)}
              >
                {removeMemberLoadingId === String(memberToRemove.userId) ? text.removingUser : text.removeUser}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
