import { useEffect, useState } from "react";
import { madorAPI, userAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";

export default function Madors() {
  const { userRole, currentUser } = useAuth();
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [createName, setCreateName] = useState("");
  const [createLoading, setCreateLoading] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [deleteSuccess, setDeleteSuccess] = useState("");
  const [deleteLoadingId, setDeleteLoadingId] = useState("");

  // Member management modal state
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [allUsers, setAllUsers] = useState([]);
  const [addUserId, setAddUserId] = useState("");
  const [modalError, setModalError] = useState("");
  const [modalLoading, setModalLoading] = useState(false);

  const isSuperAdmin = userRole === "super_admin";
  const isAdmin = userRole === "admin";
  const canManage = isSuperAdmin || isAdmin;

  const getGroupId = (group) => String(group?.UUID || group?.id || "");

  const resolveMember = (memberRef) => {
    if (memberRef && typeof memberRef === "object" && memberRef.UUID) {
      return memberRef;
    }

    const memberUUID = String(memberRef || "");
    const found = allUsers.find((u) => String(u.UUID) === memberUUID);
    if (found) {
      return found;
    }

    return {
      UUID: memberUUID,
      username: memberUUID ? memberUUID.slice(0, 8) : "Unknown",
      role: "agent",
      s_id: "",
    };
  };

  const normalizeGroup = (group) => {
    const members = (group?.members || []).map(resolveMember);
    return {
      ...group,
      id: getGroupId(group),
      members,
    };
  };

  const loadGroups = async () => {
    try {
      setLoading(true);
      setError("");
      const response = await madorAPI.listMadors();
      setGroups((response.data || []).map(normalizeGroup));
    } catch (err) {
      const message = err.response?.data?.detail || "Failed to load madors.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadGroups();
  }, []);

  useEffect(() => {
    if (canManage) {
      userAPI.getAllUsers()
        .then((res) => setAllUsers(res.data || []))
        .catch(() => {});
    }
  }, [canManage]);

  const handleCreateGroup = async (e) => {
    e.preventDefault();

    if (!isSuperAdmin) {
      setCreateError("Only super_admin can create a group.");
      return;
    }

    const trimmed = createName.trim();
    if (!trimmed) {
      setCreateError("Group name is required.");
      return;
    }

    try {
      setCreateLoading(true);
      setCreateError("");
      setCreateSuccess("");
      await madorAPI.createMador({ name: trimmed });
      setCreateName("");
      setCreateSuccess("Mador created successfully.");
      await loadGroups();
    } catch (err) {
      const message = err.response?.data?.detail || "Failed to create mador.";
      setCreateError(message);
    } finally {
      setCreateLoading(false);
    }
  };

  const handleGroupDoubleClick = (group) => {
    const canManageThis = canManage;
    if (!canManageThis) return;
    setSelectedGroup(normalizeGroup(group));
    setModalError("");
    setAddUserId("");
  };

  const handleDeleteGroup = async (group) => {
    if (!canManage) {
      setDeleteError("Only admin or super_admin can delete madors.");
      return;
    }

    try {
      const groupId = getGroupId(group);
      setDeleteLoadingId(groupId);
      setDeleteError("");
      setDeleteSuccess("");
      await madorAPI.deleteMador(groupId);
      setGroups((prev) => prev.filter((g) => getGroupId(g) !== groupId));
      if (selectedGroup && getGroupId(selectedGroup) === groupId) {
        setSelectedGroup(null);
      }
      setDeleteSuccess(`Group ${group.name} deleted successfully.`);
    } catch (err) {
      setDeleteError(err.response?.data?.detail || "Failed to delete mador.");
    } finally {
      setDeleteLoadingId("");
    }
  };

  const handleAddMember = async () => {
    if (!addUserId || !selectedGroup) return;
    try {
      setModalLoading(true);
      setModalError("");
      const selectedUser = allUsers.find((u) => String(u.UUID) === String(addUserId));
      if (!selectedUser?.s_id) {
        setModalError("Selected user is missing s_id.");
        return;
      }
      const res = await madorAPI.addMember(getGroupId(selectedGroup), selectedUser.s_id);
      const updated = normalizeGroup(res.data);
      setSelectedGroup(updated);
      setAddUserId("");
      setGroups((prev) => prev.map((g) => (getGroupId(g) === getGroupId(updated) ? updated : g)));
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to add member.");
    } finally {
      setModalLoading(false);
    }
  };

  const handleRemoveMember = async (memberUUID) => {
    if (!selectedGroup) return;
    try {
      setModalLoading(true);
      setModalError("");
      const member = allUsers.find((u) => String(u.UUID) === String(memberUUID));
      if (!member?.s_id) {
        setModalError("Member s_id not found.");
        return;
      }
      const res = await madorAPI.removeMember(getGroupId(selectedGroup), member.s_id);
      const updated = normalizeGroup(res.data);
      setSelectedGroup(updated);
      setGroups((prev) => prev.map((g) => (getGroupId(g) === getGroupId(updated) ? updated : g)));
    } catch (err) {
      setModalError(err.response?.data?.detail || "Failed to remove member.");
    } finally {
      setModalLoading(false);
    }
  };

  const availableAgents = allUsers.filter(
    (u) =>
      u.role === "agent" &&
      !selectedGroup?.members?.some((m) => String(m.UUID) === String(u.UUID))
  );

  useEffect(() => {
    if (!createError && !createSuccess && !deleteError && !deleteSuccess) {
      return;
    }

    const timer = setTimeout(() => {
      setCreateError("");
      setCreateSuccess("");
      setDeleteError("");
      setDeleteSuccess("");
    }, 3500);

    return () => clearTimeout(timer);
  }, [createError, createSuccess, deleteError, deleteSuccess]);

  return (
    <div className="page">
      <h2 className="page-header">Madors</h2>

      {isSuperAdmin ? (
        <div className="card">
          <h3 className="card-title">Create Group</h3>
          <form className="group-create-form" onSubmit={handleCreateGroup}>
            <input
              type="text"
              className="search-input"
              placeholder="Enter mador name"
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              maxLength={120}
            />
            <button className="search-button" type="submit" disabled={createLoading}>
              {createLoading ? "Creating..." : "Create Mador"}
            </button>
          </form>
          {createError ? <div className="error-banner">{createError}</div> : null}
          {createSuccess ? <div className="success-banner">{createSuccess}</div> : null}
          {deleteError ? <div className="error-banner">{deleteError}</div> : null}
          {deleteSuccess ? <div className="success-banner">{deleteSuccess}</div> : null}
        </div>
      ) : (
        <div className="card">
          <div className="empty-state">Only super_admin can create a mador.</div>
          {deleteError ? <div className="error-banner">{deleteError}</div> : null}
          {deleteSuccess ? <div className="success-banner">{deleteSuccess}</div> : null}
        </div>
      )}

      <div className="card fill">
        <h3 className="card-title">All Madors ({groups.length})</h3>

        {canManage && (
          <p className="info-hint">Double-click a group to manage its members.</p>
        )}

        {loading ? <div className="empty-state">Loading madors...</div> : null}
        {error ? <div className="error-banner">{error}</div> : null}

        {!loading && !error ? (
          <div className="meetings-list">
            {groups.length === 0 ? (
              <div className="empty-state">No madors found.</div>
            ) : (
              groups.map((group) => {
                const canManageThis = canManage;
                return (
                  <div
                    key={getGroupId(group)}
                    className={`meeting-row${canManageThis ? " group-clickable" : ""}`}
                    onDoubleClick={() => handleGroupDoubleClick(group)}
                    title={canManageThis ? "Double-click to manage members" : ""}
                  >
                    <div>
                      <div className="meeting-title">{group.name}</div>
                      <div className="meeting-meta">
                        Creator: {group.creator?.username || "-"} &bull; Members:{" "}
                        {group.members?.length || 0} &bull; Meetings:{" "}
                        {group.meetings?.length || 0}
                      </div>
                    </div>
                    {canManageThis && (
                      <div className="meeting-actions">
                        <span className="badge-manage">Manage</span>
                        <button
                          className="btn-danger"
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteGroup(group);
                          }}
                          disabled={deleteLoadingId === getGroupId(group)}
                        >
                          {deleteLoadingId === getGroupId(group) ? "Deleting..." : "Delete"}
                        </button>
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        ) : null}
      </div>

      {selectedGroup && (
        <div className="modal-overlay" onClick={() => setSelectedGroup(null)}>
          <div
            className="modal-card"
            style={{ width: 520, maxWidth: "calc(100vw - 32px)" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginBottom: 16,
              }}
            >
              <h3 className="modal-title" style={{ margin: 0 }}>
                Manage Members &mdash; {selectedGroup.name}
              </h3>
              <button
                className="btn-secondary"
                onClick={() => setSelectedGroup(null)}
                style={{ lineHeight: 1, padding: "4px 10px" }}
              >
                &#x2715;
              </button>
            </div>

            {modalError && <div className="error-banner">{modalError}</div>}

            <h4 style={{ margin: "0 0 8px 0", fontSize: 14, color: "var(--text-700)" }}>
              Current Members ({selectedGroup.members?.length || 0})
            </h4>

            {!selectedGroup.members?.length ? (
              <div className="empty-state" style={{ marginBottom: 16 }}>
                No members yet.
              </div>
            ) : (
              <div className="meetings-list" style={{ maxHeight: 200, marginBottom: 16 }}>
                {selectedGroup.members.map((member) => (
                  <div key={member.UUID} className="meeting-row">
                    <div>
                      <div className="meeting-title">{member.username}</div>
                      <div className="meeting-meta">{member.role}</div>
                    </div>
                    <div className="meeting-actions">
                      <button
                        className="btn-danger"
                        onClick={() => handleRemoveMember(member.UUID)}
                        disabled={modalLoading}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <h4 style={{ margin: "0 0 8px 0", fontSize: 14, color: "var(--text-700)" }}>
              Add Agent
            </h4>
            {availableAgents.length === 0 ? (
              <div className="empty-state">No available agents to add.</div>
            ) : (
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <select
                  className="search-input"
                  value={addUserId}
                  onChange={(e) => setAddUserId(e.target.value)}
                  style={{ flex: 1 }}
                >
                  <option value="">Select an agent...</option>
                  {availableAgents.map((u) => (
                    <option key={u.UUID} value={u.UUID}>
                      {u.username} ({u.s_id})
                    </option>
                  ))}
                </select>
                <button
                  className="search-button"
                  onClick={handleAddMember}
                  disabled={modalLoading || !addUserId}
                >
                  {modalLoading ? "..." : "Add"}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
