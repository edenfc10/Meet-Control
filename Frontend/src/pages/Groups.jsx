// Groups Page - ניהול קבוצות
// תומך ב: יצירה, מחיקה, עריכת שם, ניהול חברים + access_level, שיוך פגישות

import { useEffect, useMemo, useState } from "react";
import { groupAPI, userAPI, meetingAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Groups.css";

const ACCESS_LEVELS = ["audio", "video", "blast_dial"];

// היררכיית roles: super_admin > admin > agent > viewer
const ROLE_HIERARCHY = { super_admin: 4, admin: 3, agent: 2, viewer: 1 };

export default function Groups() {
  const { currentUser } = useAuth();
  const role = currentUser?.role;
  const myUUID = currentUser?.UUID || currentUser?.uuid;
  const myLevel = ROLE_HIERARCHY[role] || 0;
  const isAdmin = role === "admin" || role === "super_admin";
  const isAgent = role === "agent";
  // viewer לא יכול לנהל חברים בכלל
  const canManageMembers = myLevel >= 2;

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

  // הוספת חבר
  const [allUsers, setAllUsers] = useState([]);
  const [addUserId, setAddUserId] = useState("");
  const [addAccessLevels, setAddAccessLevels] = useState(["audio"]);
  const [addMemberLoading, setAddMemberLoading] = useState(false);

  // שיוך פגישה
  const [allMeetings, setAllMeetings] = useState([]);
  const [addMeetingId, setAddMeetingId] = useState("");
  const [addMeetingLoading, setAddMeetingLoading] = useState(false);
  const [removeMeetingId, setRemoveMeetingId] = useState(null);
  const [removeMeetingLoading, setRemoveMeetingLoading] = useState(false);

  const getMemberAccessLevels = (memberUuid) => {
    const rows = selectedGroup?.member_access_levels || [];
    return Array.from(
      new Set(
        rows
          .filter((row) => String(row.user_id) === String(memberUuid))
          .map((row) => row.access_level)
      )
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

  // --- טעינת כל הקבוצות ---
  const fetchGroups = async () => {
    try {
      setError("");
      const resp = await groupAPI.listGroups();
      setGroups(resp.data || []);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load groups.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchGroups(); }, []);

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
      setCreateError(err.response?.data?.detail || "Failed to create group.");
    } finally {
      setCreateLoading(false);
    }
  };

  // --- מחיקת קבוצה ---
  const handleDelete = async (groupUUID) => {
    if (!window.confirm("האם אתה בטוח שברצונך למחוק קבוצה זו?")) return;
    try {
      await groupAPI.deleteGroup(groupUUID);
      await fetchGroups();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete group.");
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
      setError(err.response?.data?.detail || "Failed to update group.");
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
    setAddAccessLevels(["audio"]);
    try {
      const [membersResp, usersResp, meetingsResp] = await Promise.allSettled([
        groupAPI.getGroupMembers(group.UUID),
        userAPI.getAllUsers(),
        meetingAPI.getAllMeetings(),
      ]);
      const members = membersResp.status === "fulfilled" ? (membersResp.value.data || []) : [];
      setModalMembers(members);
      const users = usersResp.status === "fulfilled" ? (usersResp.value.data || []) : [];
      setAllUsers(users);
      const meetings = meetingsResp.status === "fulfilled" ? (meetingsResp.value.data || []) : [];
      setAllMeetings(meetings);
      const firstError = [membersResp, usersResp, meetingsResp].find(r => r.status === "rejected");
      if (firstError) {
        const msg = firstError.reason?.response?.data?.detail;
        if (msg) setModalError(msg);
      }
    } catch (err) {
      setModalError("Failed to load group data.");
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

  // --- הוספת חבר ---
  const handleAddMember = async () => {
    if (!addUserId || !selectedGroup) return;
    if (addAccessLevels.length === 0) {
      setModalError("Select at least one meeting type.");
      return;
    }
    // מניעת שיוך עצמי לקבוצה
    if (addUserId === currentUser?.UUID) {
      setModalError("You cannot add yourself to a group.");
      return;
    }
    setAddMemberLoading(true);
    setModalError("");
    try {
      const responses = await Promise.all(
        addAccessLevels.map((level) =>
          groupAPI.addMember(selectedGroup.UUID, addUserId, level)
        )
      );
      // רענון חברים ורשימת משתמשים
      const [membersResp, usersResp] = await Promise.all([
        groupAPI.getGroupMembers(selectedGroup.UUID),
        userAPI.getAllUsers(),
      ]);
      const members = membersResp.data || [];
      setModalMembers(members);
      setAllUsers(usersResp.data || []);
      const latestGroup = responses[responses.length - 1]?.data;
      if (latestGroup) {
        setSelectedGroup(latestGroup);
      }
      setAddUserId("");
      setAddAccessLevels(["audio"]);
      await fetchGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to add member.");
    } finally {
      setAddMemberLoading(false);
    }
  };

  // --- הסרת חבר ---
  const handleRemoveMember = async (userId) => {
    if (!selectedGroup) return;
    // מניעת הסרה עצמית מקבוצה
    if (userId === currentUser?.UUID) {
      setModalError("You cannot remove yourself from a group.");
      return;
    }
    setModalError("");
    try {
      await groupAPI.removeMember(selectedGroup.UUID, userId);
      const [membersResp, usersResp] = await Promise.all([
        groupAPI.getGroupMembers(selectedGroup.UUID),
        userAPI.getAllUsers(),
      ]);
      const members = membersResp.data || [];
      setModalMembers(members);
      setAllUsers(usersResp.data || []);
      await fetchGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to remove member.");
    }
  };

  const handleRemoveMemberAccess = async (userId, accessLevel) => {
    if (!selectedGroup) return;
    if (userId === currentUser?.UUID) {
      setModalError("You cannot remove your own access from a group.");
      return;
    }
    setModalError("");
    try {
      await groupAPI.removeMemberAccess(selectedGroup.UUID, userId, accessLevel);
      const [membersResp, usersResp] = await Promise.all([
        groupAPI.getGroupMembers(selectedGroup.UUID),
        userAPI.getAllUsers(),
      ]);
      const members = membersResp.data || [];
      setModalMembers(members);
      setAllUsers(usersResp.data || []);
      const groupResp = await groupAPI.getGroup(selectedGroup.UUID);
      setSelectedGroup(groupResp.data);
      await fetchGroups();
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to remove meeting type.");
    }
  };

  // --- שיוך פגישה לקבוצה ---
  const handleAddMeeting = async () => {
    if (!addMeetingId || !selectedGroup) return;
    setAddMeetingLoading(true);
    setModalError("");
    try {
      await groupAPI.addMeeting(selectedGroup.UUID, addMeetingId);
      setAddMeetingId("");
      const resp = await groupAPI.listGroups();
      const updated = (resp.data || []).find((g) => g.UUID === selectedGroup.UUID);
      if (updated) { setSelectedGroup(updated); setGroups(resp.data || []); }
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to add meeting.");
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
      const updated = (resp.data || []).find((g) => g.UUID === selectedGroup.UUID);
      if (updated) { setSelectedGroup(updated); setGroups(resp.data || []); }
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to remove meeting.");
    }
  };

  return (
    <div className="page groups-page">
      <h2 className="page-header">Groups</h2>

      {/* כרטיס יצירת קבוצה — admin/super_admin בלבד */}
      {isAdmin && (
        <section className="card groups-create-card">
          <h3>Create Group</h3>
          <div className="groups-create-row">
            <input
              className="groups-input"
              type="text"
              placeholder="Enter group name"
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
            <button
              className="btn-primary"
              onClick={handleCreate}
              disabled={createLoading || !newGroupName.trim()}
            >
              {createLoading ? "Creating..." : "Create Group"}
            </button>
          </div>
          {createError && <div className="groups-error">{createError}</div>}
        </section>
      )}

      {/* רשימת קבוצות */}
      <section className="card groups-list-card">
        <h3>All Groups ({filteredGroups.length}{filteredGroups.length !== groups.length ? ` of ${groups.length}` : ""})</h3>

        <div className="users-filter-row">
          <input
            className="search-input"
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by group name..."
          />
          <button className="btn-secondary" type="button" onClick={() => { setSearch(""); fetchGroups(); }}>
            Refresh
          </button>
        </div>

        <p className="groups-hint">Click "Manage" to view and manage group members and meetings.</p>

        {loading ? (
          <div className="groups-empty">Loading groups...</div>
        ) : error ? (
          <div className="groups-error">{error}</div>
        ) : filteredGroups.length === 0 ? (
          <div className="groups-empty">{groups.length === 0 ? "No groups found." : "No groups match your search."}</div>
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
                        onKeyDown={(e) => e.key === "Enter" && handleUpdate(group.UUID)}
                        autoFocus
                      />
                      <button className="btn-primary" onClick={() => handleUpdate(group.UUID)}>Save</button>
                      <button className="btn-ghost" onClick={() => setEditingGroup(null)}>Cancel</button>
                    </div>
                  ) : (
                    <>
                      <strong className="group-name">{group.name}</strong>
                      <span className="group-meta">
                        Members: {getGroupMemberCount(group)} &bull; Meetings: {group.meetings?.length ?? 0}
                      </span>
                    </>
                  )}
                </div>
                <div className="group-actions">
                  <button
                    className="btn-manage"
                    onClick={() => openModal(group)}
                  >
                    Manage
                  </button>
                  {isAdmin && editingGroup !== group.UUID && (
                    <button
                      className="btn-ghost"
                      onClick={() => { setEditingGroup(group.UUID); setEditName(group.name); }}
                    >
                      Edit Name
                    </button>
                  )}
                  {isAdmin && (
                    <button
                      className="btn-danger"
                      onClick={() => handleDelete(group.UUID)}
                    >
                      Delete
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
              <h3>Manage: {selectedGroup.name}</h3>
              <button className="btn-ghost modal-close" onClick={closeModal}>✕</button>
            </div>

            {modalLoading ? (
              <div className="groups-empty">Loading...</div>
            ) : (
              <div className="groups-modal-body">
                {modalError && <div className="groups-error">{modalError}</div>}

                {/* חברים קיימים */}
                <div className="groups-modal-section">
                  <h4>Current Members ({modalMembers.length})</h4>
                  {modalMembers.length === 0 ? (
                    <div className="groups-empty">No members yet.</div>
                  ) : (
                    <table className="groups-table">
                      <thead>
                        <tr>
                          <th>S_ID</th>
                          <th>Username</th>
                          <th>Role</th>
                          <th>Meeting Types</th>
                          {(isAdmin || isAgent) && <th></th>}
                        </tr>
                      </thead>
                      <tbody>
                        {modalMembers.map((member) => (
                          <tr key={member.s_id}>
                            <td>{member.s_id}</td>
                            <td>{member.username}</td>
                            <td>
                              <span className={`role-badge role-${member.role}`}>
                                {member.role}
                              </span>
                            </td>
                            <td>
                              <div className="member-access-list">
                                {getMemberAccessLevels(member.UUID).length > 0 ? (
                                  getMemberAccessLevels(member.UUID).map((lvl) => {
                                    const canRemoveLevel = isAdmin || (isAgent && member.role === "viewer");
                                    return (
                                      <span key={`${member.UUID}-${lvl}`} className="member-access-badge member-access-pill">
                                        <span>{lvl}</span>
                                        {canRemoveLevel && (
                                          <button
                                            type="button"
                                            className="member-access-remove"
                                            onClick={() => handleRemoveMemberAccess(member.UUID || member.s_id, lvl)}
                                            title={`Remove ${lvl}`}
                                          >
                                            ×
                                          </button>
                                        )}
                                      </span>
                                    );
                                  })
                                ) : (
                                  <span className="groups-empty">No access levels</span>
                                )}
                              </div>
                            </td>
                            {(isAdmin || (isAgent && member.role === "viewer")) && (
                              <td>
                                <button
                                  className="btn-danger btn-sm"
                                  onClick={() => handleRemoveMember(member.UUID || member.s_id)}
                                >
                                  Remove User
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
                      Add Member
                      {role === "agent" ? " (Viewers only)" : role === "admin" ? " (Agent & Viewer)" : ""}
                    </h4>
                    {allUsers.filter((u) => {
                      const uLevel = ROLE_HIERARCHY[u.role] || 0;
                      // לא מציג את עצמך, ולא מציג users עם role גבוה או שווה
                      return u.UUID !== myUUID && uLevel < myLevel;
                    }).length === 0 ? (
                      <div className="groups-empty">
                        No users available to add.
                      </div>
                    ) : (
                      <div className="groups-add-row">
                        <select
                          className="groups-select"
                          value={addUserId}
                          onChange={(e) => setAddUserId(e.target.value)}
                        >
                          <option value="">Select user...</option>
                          {allUsers
                            .filter((u) => {
                              const uLevel = ROLE_HIERARCHY[u.role] || 0;
                              return u.UUID !== myUUID && uLevel < myLevel;
                            })
                            .map((u) => (
                              <option key={u.UUID} value={u.UUID}>
                                {u.username} ({u.s_id}) — {u.role}
                              </option>
                            ))}
                        </select>
                        {canManageMembers && (
                          <div className="groups-access-segmented" role="group" aria-label="Meeting types">
                            {ACCESS_LEVELS.map((lvl) => {
                              const active = addAccessLevels.includes(lvl);
                              return (
                                <button
                                  key={lvl}
                                  type="button"
                                  className={`groups-segment-btn ${active ? "is-active" : ""}`}
                                  onClick={() => {
                                    if (active) {
                                      setAddAccessLevels((prev) => prev.filter((x) => x !== lvl));
                                    } else {
                                      setAddAccessLevels((prev) => [...prev, lvl]);
                                    }
                                  }}
                                >
                                  {lvl}
                                </button>
                              );
                            })}
                          </div>
                        )}
                        <button
                          className="btn-primary"
                          onClick={handleAddMember}
                          disabled={addMemberLoading || !addUserId || addAccessLevels.length === 0}
                        >
                          {addMemberLoading ? "Adding..." : "Add"}
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {/* שיוך פגישה */}
                {isAdmin && (
                  <div className="groups-modal-section">
                    <h4>Meetings ({selectedGroup.meetings?.length ?? 0})</h4>
                    {/* פגישות קיימות בקבוצה */}
                    {selectedGroup.meetings?.length > 0 && (
                      <table className="groups-table">
                        <thead>
                          <tr>
                            <th>Meeting #</th>
                            <th>Type</th>
                            <th></th>
                          </tr>
                        </thead>
                        <tbody>
                          {selectedGroup.meetings.map((mId) => {
                            const meeting = allMeetings.find((m) => m.UUID === mId || m.UUID === String(mId));
                            return (
                              <tr key={mId}>
                                <td>{meeting ? `#${meeting.m_number}` : String(mId).slice(0, 8) + "..."}</td>
                                <td>{meeting ? meeting.accessLevel : "—"}</td>
                                <td>
                                  <button
                                    className="btn-danger btn-sm"
                                    onClick={() => handleRemoveMeeting(String(mId))}
                                  >
                                    Remove
                                  </button>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    )}
                    {/* הוספת פגישה */}
                    <div className="groups-add-row" style={{ marginTop: "8px" }}>
                      <select
                        className="groups-select"
                        value={addMeetingId}
                        onChange={(e) => setAddMeetingId(e.target.value)}
                      >
                        <option value="">Add meeting...</option>
                        {allMeetings
                          .filter((m) => !selectedGroup.meetings?.map(String).includes(String(m.UUID)))
                          .map((m) => (
                            <option key={m.UUID} value={m.UUID}>
                              #{m.m_number} ({m.accessLevel})
                            </option>
                          ))}
                      </select>
                      <button
                        className="btn-primary"
                        onClick={handleAddMeeting}
                        disabled={addMeetingLoading || !addMeetingId}
                      >
                        {addMeetingLoading ? "Adding..." : "Add"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
