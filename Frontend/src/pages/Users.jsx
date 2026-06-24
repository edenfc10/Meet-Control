// ============================================================================
// Users Page - ניהול משתמשים
// ============================================================================
// דף זה מאפשר:
//   - צפייה בכל המשתמשים עם חיפוש וסינון לפי תפקיד
//   - יצירת משתמש חדש (admin יוצר agent, super_admin יוצר agent/admin)
//   - מחיקת משתמש (לא מוחק את עצמו, admin לא מוחק super_admin)
// ============================================================================

import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { userAPI } from "../services/api";

export default function Users({ language = "en" }) {
  const { currentUser } = useAuth();
  const isHebrew = language === "he";
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(true);
  const [usersError, setUsersError] = useState("");

  const [searchText, setSearchText] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");

  const [formData, setFormData] = useState({
    s_id: "",
    username: "",
    password: "",
    role: "agent",
  });
  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");
  const [deleteError, setDeleteError] = useState("");
  const [deleteSuccess, setDeleteSuccess] = useState("");
  const [deleteLoadingSid, setDeleteLoadingSid] = useState("");

  const [editingUser, setEditingUser] = useState(null);
  const [editFormData, setEditFormData] = useState({
    s_id: "",
    username: "",
    password: "",
    role: "",
  });
  const [editError, setEditError] = useState("");
  const [editSuccess, setEditSuccess] = useState("");
  const [editSubmitting, setEditSubmitting] = useState(false);

  const [userToDelete, setUserToDelete] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const canCreateUsers =
    currentUser?.role === "super_admin" || currentUser?.role === "admin";
  const canDeleteUsers =
    currentUser?.role === "super_admin" || currentUser?.role === "admin";

  const text = {
    pageTitle: isHebrew ? "משתמשים" : "Users",
    createTitle: isHebrew ? "יצירת משתמש חדש" : "Create New User",
    sidPlaceholder: "S_ID",
    usernamePlaceholder: isHebrew ? "שם משתמש" : "Username",
    passwordPlaceholder: isHebrew ? "סיסמה" : "Password",
    createButton: submitting
      ? isHebrew
        ? "יוצר..."
        : "Creating..."
      : isHebrew
        ? "צור משתמש"
        : "Create User",
    directoryTitle: isHebrew ? "רשימת משתמשים" : "Users Directory",
    searchPlaceholder: isHebrew
      ? "חיפוש לפי S_ID או שם משתמש"
      : "Search by S_ID or username",
    roleFilterAll: isHebrew ? "כל התפקידים" : "Type Role",
    refresh: isHebrew ? "רענון" : "Refresh",
    loadingUsers: isHebrew ? "טוען משתמשים..." : "Loading users...",
    noUsers: isHebrew
      ? "לא נמצאו משתמשים לפי הסינון הזה."
      : "No users found for this filter.",
    sidLabel: "S_ID",
    edit: isHebrew ? "עריכה" : "Edit",
    editTitle: isHebrew ? "ערוך משתמש" : "Edit user",
    delete: isHebrew ? "מחיקה" : "Delete",
    deleteTitle: isHebrew ? "מחק משתמש" : "Delete user",
    deleting: isHebrew ? "מוחק..." : "Deleting...",
    deleteModalTitle: isHebrew ? "מחיקת משתמש" : "Delete User",
    deleteModalMessage: isHebrew
      ? "האם למחוק את המשתמש"
      : "Are you sure you want to delete user",
    cancel: isHebrew ? "ביטול" : "Cancel",
    deleteUser: isHebrew ? "מחק משתמש" : "Delete User",
    editModalTitle: isHebrew ? "עריכת משתמש" : "Edit User",
    newPasswordPlaceholder: isHebrew
      ? "סיסמה חדשה (אם לא משנים משאירים ריק)"
      : "New Password (leave blank to keep)",
    updateUser: editSubmitting
      ? isHebrew
        ? "מעדכן..."
        : "Updating..."
      : isHebrew
        ? "עדכן משתמש"
        : "Update User",
  };

  const roleOptions = useMemo(() => {
    if (currentUser?.role === "super_admin") {
      return ["admin", "agent", "viewer"];
    }
    if (currentUser?.role === "admin") {
      return ["agent", "viewer"];
    }
    return [];
  }, [currentUser?.role]);

  const visibleUsers = useMemo(() => {
    const query = searchText.trim().toLowerCase();

    const usersForRole =
      currentUser?.role === "super_admin"
        ? users
        : users.filter((user) => user.role !== "super_admin");

    return usersForRole.filter((user) => {
      const matchRole = roleFilter === "all" || user.role === roleFilter;
      if (!matchRole) {
        return false;
      }

      if (!query) {
        return true;
      }

      const bySid = (user.s_id || "").toLowerCase().includes(query);
      const byUsername = (user.username || "").toLowerCase().includes(query);
      return bySid || byUsername;
    });
  }, [users, searchText, roleFilter, currentUser?.role]);

  const fetchUsers = async () => {
    try {
      setUsersLoading(true);
      setUsersError("");
      const response = await userAPI.getAllUsers();
      setUsers(response.data || []);
    } catch (err) {
      setUsers([]);
      setUsersError(
        err.response?.data?.detail ||
          (isHebrew ? "טעינת המשתמשים נכשלה." : "Failed to load users."),
      );
    } finally {
      setUsersLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!canCreateUsers) {
      setCreateError(
        isHebrew
          ? "אין לך הרשאה ליצור משתמשים."
          : "You are not allowed to create users.",
      );
      return;
    }

    if (
      !formData.s_id.trim() ||
      !formData.username.trim() ||
      !formData.password.trim()
    ) {
      setCreateError(
        isHebrew ? "חובה למלא את כל השדות." : "All fields are required.",
      );
      return;
    }

    if (!roleOptions.includes(formData.role)) {
      setCreateError(
        isHebrew
          ? "אין לך הרשאה ליצור את התפקיד הזה."
          : "You are not allowed to create this role.",
      );
      return;
    }

    const payload = {
      s_id: formData.s_id.trim(),
      username: formData.username.trim(),
      password: formData.password,
    };

    try {
      setSubmitting(true);
      setCreateError("");
      setCreateSuccess("");

      if (formData.role === "admin") {
        await userAPI.createAdmin(payload);
      } else if (formData.role === "viewer") {
        await userAPI.createViewer(payload);
      } else {
        await userAPI.createAgent(payload);
      }

      setCreateSuccess(
        isHebrew
          ? `המשתמש נוצר בהצלחה עם תפקיד ${formData.role}.`
          : `${formData.role} user created successfully.`,
      );
      setFormData({
        s_id: "",
        username: "",
        password: "",
        role: roleOptions[0] || "agent",
      });
      await fetchUsers();
    } catch (err) {
      setCreateError(
        err.response?.data?.detail ||
          (isHebrew ? "יצירת המשתמש נכשלה." : "Failed to create user."),
      );
    } finally {
      setSubmitting(false);
    }
  };

  const canDeleteTarget = (targetUser) => {
    if (!canDeleteUsers || !targetUser) {
      return false;
    }

    if ((targetUser.s_id || "") === (currentUser?.s_id || "")) {
      return false;
    }

    if (currentUser?.role === "admin" && targetUser.role === "super_admin") {
      return false;
    }

    return true;
  };

  const canEditUser = (targetUser) => {
    return (
      canCreateUsers &&
      targetUser &&
      (targetUser.s_id || "") !== (currentUser?.s_id || "")
    );
  };

  const openEditModal = (user) => {
    if (!canEditUser(user)) {
      setEditError(
        isHebrew
          ? "אין לך הרשאה לערוך את המשתמש הזה."
          : "You are not allowed to edit this user.",
      );
      return;
    }

    setEditingUser(user);
    setEditFormData({
      s_id: user.s_id || "",
      username: user.username || "",
      password: "",
      role: user.role || "",
    });
    setEditError("");
    setEditSuccess("");
  };

  const closeEditModal = () => {
    setEditingUser(null);
    setEditFormData({ username: "", password: "", role: "" });
    setEditError("");
    setEditSuccess("");
  };

  const handleEditChange = (e) => {
    const { name, value } = e.target;
    setEditFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();

    if (!editingUser) {
      setEditError(
        isHebrew ? "לא נבחר משתמש לעריכה." : "No user selected for editing.",
      );
      return;
    }

    if (!editFormData.username.trim()) {
      setEditError(isHebrew ? "חובה להזין שם משתמש." : "Username is required.");
      return;
    }

    try {
      setEditSubmitting(true);
      setEditError("");
      setEditSuccess("");

      await userAPI.updateUser(editingUser.UUID, {
        s_id:
          editFormData.s_id.trim() !== editingUser.s_id
            ? editFormData.s_id.trim()
            : undefined,
        username: editFormData.username.trim(),
        password: editFormData.password || undefined,
        role:
          editFormData.role !== editingUser.role
            ? editFormData.role
            : undefined,
      });

      setEditSuccess(
        isHebrew ? "המשתמש עודכן בהצלחה." : "User updated successfully.",
      );
      await fetchUsers();
      setTimeout(closeEditModal, 1500);
    } catch (err) {
      setEditError(
        err.response?.data?.detail ||
          (isHebrew ? "עדכון המשתמש נכשל." : "Failed to update user."),
      );
    } finally {
      setEditSubmitting(false);
    }
  };

  const openDeleteConfirm = (targetUser) => {
    if (!canDeleteTarget(targetUser)) {
      setDeleteError(
        isHebrew
          ? "אין לך הרשאה למחוק את המשתמש הזה."
          : "You are not allowed to delete this user.",
      );
      return;
    }
    setUserToDelete(targetUser);
    setShowDeleteConfirm(true);
  };

  const closeDeleteConfirm = () => {
    setUserToDelete(null);
    setShowDeleteConfirm(false);
  };

  const confirmDeleteUser = async () => {
    if (!userToDelete) return;

    try {
      setDeleteLoadingSid(userToDelete.s_id);
      setDeleteError("");
      setDeleteSuccess("");

      await userAPI.deleteUser(userToDelete.s_id);
      setDeleteSuccess(
        isHebrew
          ? `המשתמש ${userToDelete.username} נמחק בהצלחה.`
          : `User ${userToDelete.username} deleted successfully.`,
      );
      await fetchUsers();
      closeDeleteConfirm();
    } catch (err) {
      setDeleteError(
        err.response?.data?.detail ||
          (isHebrew ? "מחיקת המשתמש נכשלה." : "Failed to delete user."),
      );
    } finally {
      setDeleteLoadingSid("");
    }
  };

  useEffect(() => {
    if (
      !createError &&
      !createSuccess &&
      !deleteError &&
      !deleteSuccess &&
      !editError &&
      !editSuccess
    ) {
      return;
    }

    const timer = setTimeout(() => {
      setCreateError("");
      setCreateSuccess("");
      setDeleteError("");
      setDeleteSuccess("");
      setEditError("");
      setEditSuccess("");
    }, 3500);

    return () => clearTimeout(timer);
  }, [
    createError,
    createSuccess,
    deleteError,
    deleteSuccess,
    editError,
    editSuccess,
  ]);

  return (
    <div className="page">
      <h2 className="page-header">{text.pageTitle}</h2>

      {canCreateUsers ? (
        <div className="card">
          <h3 className="card-title">{text.createTitle}</h3>
          <form className="user-create-form" onSubmit={handleSubmit}>
            <div className="user-form-grid">
              <input
                className="search-input"
                type="text"
                name="s_id"
                placeholder={text.sidPlaceholder}
                value={formData.s_id}
                onChange={handleChange}
                required
              />
              <input
                className="search-input"
                type="text"
                name="username"
                placeholder={text.usernamePlaceholder}
                value={formData.username}
                onChange={handleChange}
                required
              />
              <input
                className="search-input"
                type="password"
                name="password"
                placeholder={text.passwordPlaceholder}
                value={formData.password}
                onChange={handleChange}
                required
              />
              <select
                className="search-select"
                name="role"
                value={formData.role}
                onChange={handleChange}
              >
                {roleOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="search-button"
              type="submit"
              disabled={submitting}
            >
              {text.createButton}
            </button>
          </form>

          {createError ? (
            <div className="error-banner">{createError}</div>
          ) : null}
          {createSuccess ? (
            <div className="success-banner">{createSuccess}</div>
          ) : null}
          {deleteError ? (
            <div className="error-banner">{deleteError}</div>
          ) : null}
          {deleteSuccess ? (
            <div className="success-banner">{deleteSuccess}</div>
          ) : null}
        </div>
      ) : null}

      <div className="card fill">
        <h3 className="card-title">{text.directoryTitle}</h3>

        <div className="users-filter-row">
          <input
            className="search-input"
            type="text"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            placeholder={text.searchPlaceholder}
          />

          <select
            className="search-select"
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
          >
            <option value="all">{text.roleFilterAll}</option>
            {currentUser?.role === "super_admin" ? (
              <option value="super_admin">super_admin</option>
            ) : null}
            <option value="admin">admin</option>
            <option value="agent">agent</option>
            <option value="viewer">viewer</option>
          </select>

          <button
            className="btn-secondary refresh-soft-button"
            type="button"
            onClick={fetchUsers}
          >
            {text.refresh}
          </button>
        </div>

        {usersError ? <div className="error-banner">{usersError}</div> : null}

        <div className="meetings-list">
          {usersLoading ? (
            <div className="empty-state">{text.loadingUsers}</div>
          ) : visibleUsers.length === 0 ? (
            <div className="empty-state">{text.noUsers}</div>
          ) : (
            visibleUsers.map((user) => (
              <div key={user.UUID} className="meeting-row">
                <div>
                  <div className="meeting-title-row">
                    <div className="meeting-title">{user.username}</div>
                    <span className={`user-role-badge role-${user.role}`}>
                      {user.role}
                    </span>
                  </div>
                  <div className="meeting-meta">
                    {text.sidLabel}: {user.s_id}
                  </div>
                </div>
                {canCreateUsers &&
                (canEditUser(user) || canDeleteTarget(user)) ? (
                  <div className="meeting-actions">
                    {canEditUser(user) ? (
                      <button
                        className="btn-secondary edit-soft-button"
                        type="button"
                        onClick={() => openEditModal(user)}
                        title={text.editTitle}
                      >
                        {text.edit}
                      </button>
                    ) : null}
                    {canDeleteUsers && canDeleteTarget(user) ? (
                      <button
                        className="btn-danger"
                        type="button"
                        onClick={() => openDeleteConfirm(user)}
                        disabled={deleteLoadingSid === user.s_id}
                        title={text.deleteTitle}
                      >
                        {deleteLoadingSid === user.s_id
                          ? text.deleting
                          : text.delete}
                      </button>
                    ) : null}
                  </div>
                ) : null}
              </div>
            ))
          )}
        </div>
      </div>

      {showDeleteConfirm && userToDelete ? (
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
              {text.deleteModalMessage} "{userToDelete.username}"?
            </p>

            <div className="modal-actions">
              <button
                className="btn-secondary"
                type="button"
                onClick={closeDeleteConfirm}
                disabled={deleteLoadingSid === userToDelete.s_id}
              >
                {text.cancel}
              </button>
              <button
                className="btn-danger"
                type="button"
                onClick={confirmDeleteUser}
                disabled={deleteLoadingSid === userToDelete.s_id}
              >
                {deleteLoadingSid === userToDelete.s_id
                  ? text.deleting
                  : text.deleteUser}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {editingUser ? (
        <div className="modal-overlay" onClick={closeEditModal}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <h3 className="modal-title">
              {text.editModalTitle}: {editingUser.username}
            </h3>

            <form className="user-create-form" onSubmit={handleEditSubmit}>
              <div className="user-form-grid">
                <input
                  className="search-input"
                  type="text"
                  name="s_id"
                  placeholder={text.sidPlaceholder}
                  value={editFormData.s_id}
                  onChange={handleEditChange}
                />
                <input
                  className="search-input"
                  type="text"
                  name="username"
                  placeholder={text.usernamePlaceholder}
                  value={editFormData.username}
                  onChange={handleEditChange}
                  required
                />
                <input
                  className="search-input"
                  type="password"
                  name="password"
                  placeholder={text.newPasswordPlaceholder}
                  value={editFormData.password}
                  onChange={handleEditChange}
                />
                <select
                  className="search-select"
                  name="role"
                  value={editFormData.role}
                  onChange={handleEditChange}
                >
                  {roleOptions.map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
              </div>

              <div className="modal-actions">
                <button
                  className="btn-secondary"
                  type="button"
                  onClick={closeEditModal}
                  disabled={editSubmitting}
                >
                  {text.cancel}
                </button>
                <button
                  className="search-button"
                  type="submit"
                  disabled={editSubmitting}
                >
                  {text.updateUser}
                </button>
              </div>
            </form>

            {editError ? (
              <div className="error-banner" style={{ marginTop: "12px" }}>
                {editError}
              </div>
            ) : null}
            {editSuccess ? (
              <div className="success-banner" style={{ marginTop: "12px" }}>
                {editSuccess}
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
