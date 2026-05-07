import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { serverAPI } from "../services/api";

const SETTINGS_SECTIONS = [
  { key: "audio", label: "audio" },
  { key: "video", label: "video" },
  { key: "blast-dial", label: "blast-dial" },
];

const SECTION_TO_ACCESS_LEVEL = {
  audio: "audio",
  video: "video",
  "blast-dial": "blast_dial",
};

const ACCESS_LEVEL_TO_SECTION = {
  audio: "audio",
  video: "video",
  blast_dial: "blast-dial",
};

const ACCESS_LEVEL_HE_LABEL = {
  audio: "ועידות אודיו",
  video: "ועידות וידאו",
  blast_dial: "ועידות הזנקה",
};

const createEmptySection = () => ({
  serverName: "",
  ipAddress: "",
  port: "",
  username: "",
  password: "",
});

const createDefaultSettings = () => ({
  audio: createEmptySection(),
  video: createEmptySection(),
  "blast-dial": createEmptySection(),
});

const createDefaultSelection = () => ({
  audio: false,
  video: false,
  "blast-dial": false,
});

const createEditDraft = (server) => ({
  server_name: server.server_name,
  ip_address: server.ip_address,
  port: server.port,
  username: server.username,
  password: server.password,
  accessLevel: server.accessLevel,
  hierarchy_order: server.hierarchy_order || 0,
});

export default function Reports({ language = "en" }) {
  const { currentUser } = useAuth();
  const isHebrew = language === "he";
  const isSuperAdmin = currentUser?.role === "super_admin";
  const [settings, setSettings] = useState(createDefaultSettings);
  const [selectedSections, setSelectedSections] = useState(
    createDefaultSelection,
  );
  const [servers, setServers] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [listError, setListError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState("");
  const [editingServerUuid, setEditingServerUuid] = useState("");
  const [editDraft, setEditDraft] = useState(null);

  const text = {
    pageTitle: isHebrew ? "הגדרות" : "Settings",
    readonlyBanner: isHebrew
      ? "רק super_admin יכול לנהל הגדרות שרתים."
      : "only super_admin can manage server settings.",
    add: isHebrew ? "הוספה" : "add",
    serverName: isHebrew ? "שם שרת" : "server name",
    ipAddress: isHebrew ? "כתובת IP" : "IP address",
    port: isHebrew ? "פורט" : "port",
    username: isHebrew ? "שם משתמש" : "username",
    password: isHebrew ? "סיסמה" : "password",
    addServers: isHebrew ? "הוסף שרתים" : "add servers",
    saving: isHebrew ? "שומר..." : "saving...",
    servers: isHebrew ? "שרתים" : "Servers",
    refresh: isHebrew ? "רענון" : "refresh",
    loading: isHebrew ? "טוען..." : "loading...",
    type: isHebrew ? "סוג" : "type",
    actions: isHebrew ? "פעולות" : "actions",
    loadingServers: isHebrew ? "טוען שרתים..." : "Loading servers...",
    noServers: isHebrew ? "עדיין לא נמצאו שרתים." : "No servers found yet.",
    save: isHebrew ? "שמור" : "save",
    cancel: isHebrew ? "ביטול" : "cancel",
    edit: isHebrew ? "עריכה" : "edit",
    delete: isHebrew ? "מחיקה" : "delete",
    setPrimary: isHebrew ? "הגדר כראשי" : "Set as Primary",
    primary: isHebrew ? "ראשי" : "Primary",
    hierarchy: isHebrew ? "סדר היררכיה" : "Hierarchy Order",
    status: isHebrew ? "סטטוס" : "Status",
    testConnection: isHebrew ? "בדיקת חיבור" : "Test Connection",
    connected: isHebrew ? "מחובר" : "Connected",
    disconnected: isHebrew ? "מנותק" : "Disconnected",
    error: isHebrew ? "שגיאה" : "Error",
    pending: isHebrew ? "בבדיקה" : "Pending",
    testing: isHebrew ? "בודק..." : "Testing...",
    setPrimarySuccess: isHebrew ? "שרת הוגדר כראשי בהצלחה" : "Server set as primary successfully",
    setPrimaryError: isHebrew ? "שגיאה בהגדרת שרת כראשי" : "Error setting server as primary",
    loadServersError: isHebrew
      ? "טעינת השרתים נכשלה."
      : "Failed to load servers.",
    onlySuperAdmin: isHebrew
      ? "רק super_admin יכול לנהל שרתים."
      : "Only super_admin can manage servers.",
    selectSection: isHebrew
      ? "יש לסמן לפחות סוג שרת אחד לפני יצירה."
      : "Mark at least one server section before creating servers.",
    allFieldsFor: isHebrew
      ? "חובה למלא את כל השדות עבור שרת"
      : "All fields are required for",
    oneServerAdded: isHebrew
      ? "השרת נוסף בהצלחה."
      : "Server added successfully.",
    manyServersAddedSuffix: isHebrew
      ? "שרתים נוספו בהצלחה."
      : "servers added successfully.",
    addServerError: isHebrew ? "הוספת השרת נכשלה." : "Failed to add server.",
    allFieldsForUpdate: isHebrew
      ? "חובה למלא את כל השדות בעת עדכון שרת."
      : "All fields are required when updating a server.",
    updated: isHebrew ? "השרת עודכן בהצלחה." : "Server updated successfully.",
    updateError: isHebrew ? "עדכון השרת נכשל." : "Failed to update server.",
    deleteConfirm: isHebrew ? "למחוק את השרת הזה?" : "Delete this server?",
    deleted: isHebrew ? "השרת נמחק בהצלחה." : "Server deleted successfully.",
    deleteError: isHebrew ? "מחיקת השרת נכשלה." : "Failed to delete server.",
  };

  const formatAccessLabel = (value) => {
    if (!isHebrew) {
      return ACCESS_LEVEL_TO_SECTION[value] || value;
    }
    return ACCESS_LEVEL_HE_LABEL[value] || value;
  };

  const loadServers = async () => {
    if (!isSuperAdmin) {
      setServers([]);
      setListError("");
      return;
    }

    try {
      setIsLoading(true);
      const response = await serverAPI.getAllServers();
      setServers(Array.isArray(response.data) ? response.data : []);
      setListError("");
    } catch (error) {
      const errorMessage = error?.response?.data?.detail;
      setListError(typeof errorMessage === 'string' ? errorMessage : text.loadServersError);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (sectionKey, fieldName, value) => {
    if (!isSuperAdmin) {
      return;
    }

    setSettings((prev) => ({
      ...prev,
      [sectionKey]: {
        ...prev[sectionKey],
        [fieldName]: value,
      },
    }));
  };

  const resetSection = (sectionKey) => {
    setSettings((prev) => ({
      ...prev,
      [sectionKey]: createEmptySection(),
    }));
  };

  const toggleSectionSelection = (sectionKey, isChecked) => {
    if (!isSuperAdmin) {
      return;
    }

    setSelectedSections((prev) => ({
      ...prev,
      [sectionKey]: isChecked,
    }));
  };

  const handleSave = async () => {
    if (!isSuperAdmin) {
      setSaveError(text.onlySuperAdmin);
      setSaveSuccess("");
      return;
    }

    const sectionsToCreate = SETTINGS_SECTIONS.filter(
      (section) => selectedSections[section.key],
    );

    if (sectionsToCreate.length === 0) {
      setSaveError(text.selectSection);
      setSaveSuccess("");
      return;
    }

    const incompleteSection = sectionsToCreate.find((section) => {
      const sectionData = settings[section.key];
      return Object.values(sectionData).some((value) => !value.trim());
    });

    if (incompleteSection) {
      setSaveError(
        isHebrew
          ? `${text.allFieldsFor} ${incompleteSection.label}.`
          : `All fields are required for ${incompleteSection.label} server.`,
      );
      setSaveSuccess("");
      return;
    }

    const payloads = sectionsToCreate.map((section) => {
      const sectionData = settings[section.key];
      return {
        sectionKey: section.key,
        payload: {
          server_name: sectionData.serverName.trim(),
          ip_address: sectionData.ipAddress.trim(),
          port: parseInt(sectionData.port) || 8443,
          username: sectionData.username.trim(),
          password: sectionData.password,
          accessLevel: SECTION_TO_ACCESS_LEVEL[section.key],
        },
      };
    });

    try {
      setIsSubmitting(true);
      await Promise.all(
        payloads.map(({ payload }) => serverAPI.createServer(payload)),
      );
      payloads.forEach(({ sectionKey }) => {
        resetSection(sectionKey);
      });
      setSelectedSections(createDefaultSelection());
      await loadServers();
      setSaveSuccess(
        payloads.length === 1
          ? text.oneServerAdded
          : `${payloads.length} ${text.manyServersAddedSuffix}`,
      );
      setSaveError("");
    } catch (error) {
      const errorMessage = error?.response?.data?.detail;
      setSaveError(typeof errorMessage === 'string' ? errorMessage : text.addServerError);
      setSaveSuccess("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const startEditing = (server) => {
    setEditingServerUuid(server.UUID);
    setEditDraft(createEditDraft(server));
  };

  const cancelEditing = () => {
    setEditingServerUuid("");
    setEditDraft(null);
  };

  const handleEditChange = (fieldName, value) => {
    setEditDraft((prev) => ({
      ...prev,
      [fieldName]: value,
    }));
  };

  const handleUpdateServer = async () => {
    if (!editingServerUuid || !editDraft) {
      return;
    }

    const hasMissingField = [
      editDraft.server_name,
      editDraft.ip_address,
      editDraft.username,
      editDraft.password,
    ].some((value) => !value.trim());

    if (hasMissingField) {
      setSaveError(text.allFieldsForUpdate);
      setSaveSuccess("");
      return;
    }

    try {
      setIsSubmitting(true);
      await serverAPI.updateServer(editingServerUuid, {
        server_name: editDraft.server_name.trim(),
        ip_address: editDraft.ip_address.trim(),
        port: parseInt(editDraft.port) || 8443,
        username: editDraft.username.trim(),
        password: editDraft.password,
        accessLevel: editDraft.accessLevel,
        hierarchy_order: parseInt(editDraft.hierarchy_order) || 0,
      });
      await loadServers();
      cancelEditing();
      setSaveSuccess(text.updated);
      setSaveError("");
    } catch (error) {
      const errorMessage = error?.response?.data?.detail;
      setSaveError(typeof errorMessage === 'string' ? errorMessage : text.updateError);
      setSaveSuccess("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteServer = async (serverUuid) => {
    if (!window.confirm(text.deleteConfirm)) {
      return;
    }

    try {
      setIsSubmitting(true);
      await serverAPI.deleteServer(serverUuid);
      await loadServers();
      if (editingServerUuid === serverUuid) {
        cancelEditing();
      }
      setSaveSuccess(text.deleted);
      setSaveError("");
    } catch (error) {
      const errorMessage = error?.response?.data?.detail;
      setSaveError(typeof errorMessage === 'string' ? errorMessage : text.deleteError);
      setSaveSuccess("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSetPrimaryServer = async (serverUuid) => {
    if (!window.confirm(`האם להגדיר שרת זה כראשי?`)) {
      return;
    }

    try {
      setIsSubmitting(true);
      await serverAPI.setPrimaryServer(serverUuid);
      await loadServers();
      setSaveSuccess(text.setPrimarySuccess);
      setSaveError("");
    } catch (error) {
      const errorMessage = error?.response?.data?.detail;
      setSaveError(typeof errorMessage === 'string' ? errorMessage : text.setPrimaryError);
      setSaveSuccess("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTestConnection = async (serverUuid) => {
    try {
      setIsSubmitting(true);
      await serverAPI.testConnection(serverUuid);
      await loadServers();
      setSaveSuccess(isHebrew ? "בדיקת חיבור הושלמה" : "Connection test completed");
      setSaveError("");
    } catch (error) {
      const errorMessage = error?.response?.data?.detail;
      setSaveError(typeof errorMessage === 'string' ? errorMessage : (isHebrew ? "בדיקת חיבור נכשלה" : "Connection test failed"));
      setSaveSuccess("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusDisplay = (server) => {
    const status = server.connection_status;
    let className = "status-badge ";
    let displayText = status;

    switch (status) {
      case 'connected':
        className += "status-connected";
        displayText = text.connected;
        break;
      case 'disconnected':
        className += "status-disconnected";
        displayText = text.disconnected;
        break;
      case 'error':
        className += "status-error";
        displayText = text.error;
        break;
      case 'pending':
        className += "status-pending";
        displayText = text.pending;
        break;
      case 'testing':
        className += "status-testing";
        displayText = text.testing;
        break;
      default:
        className += "status-unknown";
        displayText = status;
    }

    return { className, displayText };
  };

  useEffect(() => {
    loadServers();
  }, [isSuperAdmin]);

  useEffect(() => {
    if (isSuperAdmin) {
      return;
    }

    setSelectedSections(createDefaultSelection());
  }, [isSuperAdmin]);

  useEffect(() => {
    if (!saveError && !saveSuccess) {
      return;
    }

    const timer = setTimeout(() => {
      setSaveError("");
      setSaveSuccess("");
    }, 3000);

    return () => clearTimeout(timer);
  }, [saveError, saveSuccess]);

  // Auto-refresh servers when there are pending servers
  useEffect(() => {
    if (!isSuperAdmin) {
      return;
    }

    const hasPendingServers = servers.some(server => 
      server.connection_status === 'pending' || server.connection_status === 'testing'
    );

    if (!hasPendingServers) {
      return;
    }

    const interval = setInterval(() => {
      loadServers();
    }, 5000); // Refresh every 5 seconds

    return () => clearInterval(interval);
  }, [servers, isSuperAdmin]);

  return (
    <div className="page settings-page">
      <h2 className="page-header">{text.pageTitle}</h2>

      <div className="card settings-form-card">
        {!isSuperAdmin ? (
          <div className="error-banner reports-readonly-banner">
            {text.readonlyBanner}
          </div>
        ) : null}

        <div className="reports-sections-grid">
          {SETTINGS_SECTIONS.map((section) => {
            const sectionData = settings[section.key] || createEmptySection();
            const isChecked = selectedSections[section.key];

            return (
              <div className="reports-section-card" key={section.key}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: "8px",
                    marginBottom: "10px",
                  }}
                >
                  <h4
                    className="reports-section-title"
                    style={{ marginBottom: 0 }}
                  >
                    {isHebrew
                      ? formatAccessLabel(SECTION_TO_ACCESS_LEVEL[section.key])
                      : section.label}
                  </h4>
                  <label
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                      fontSize: "0.9rem",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={Boolean(isChecked)}
                      onChange={(event) =>
                        toggleSectionSelection(
                          section.key,
                          event.target.checked,
                        )
                      }
                      disabled={!isSuperAdmin || isSubmitting}
                    />
                    {text.add}
                  </label>
                </div>

                <div className="reports-field-grid">
                  <input
                    className="search-input"
                    type="text"
                    placeholder={text.serverName}
                    value={sectionData.serverName}
                    onChange={(e) =>
                      handleChange(section.key, "serverName", e.target.value)
                    }
                    disabled={!isSuperAdmin}
                  />

                  <input
                    className="search-input"
                    type="text"
                    placeholder={text.ipAddress}
                    value={sectionData.ipAddress}
                    onChange={(e) =>
                      handleChange(section.key, "ipAddress", e.target.value)
                    }
                    disabled={!isSuperAdmin}
                  />

                  <input
                    className="search-input"
                    type="number"
                    placeholder={text.port}
                    value={sectionData.port}
                    onChange={(e) =>
                      handleChange(section.key, "port", e.target.value)
                    }
                    disabled={!isSuperAdmin}
                    min="1"
                    max="65535"
                  />

                  <input
                    className="search-input"
                    type="text"
                    placeholder={text.username}
                    value={sectionData.username}
                    onChange={(e) =>
                      handleChange(section.key, "username", e.target.value)
                    }
                    disabled={!isSuperAdmin}
                  />

                  <input
                    className="search-input"
                    type="password"
                    placeholder={text.password}
                    value={sectionData.password}
                    onChange={(e) =>
                      handleChange(section.key, "password", e.target.value)
                    }
                    disabled={!isSuperAdmin}
                  />
                </div>
              </div>
            );
          })}
        </div>

        {saveError ? <div className="error-banner">{saveError}</div> : null}
        {saveSuccess ? (
          <div className="success-banner">{saveSuccess}</div>
        ) : null}

        <div className="reports-actions-row">
          <button
            className="search-button"
            type="button"
            onClick={handleSave}
            disabled={!isSuperAdmin || isSubmitting}
          >
            {isSubmitting ? text.saving : text.addServers}
          </button>
        </div>
      </div>

      {isSuperAdmin ? (
        <div className="card reports-servers-card settings-servers-card">
          <div className="reports-table-header-row">
            <h3 className="card-title">{text.servers}</h3>
            <button
              className="search-button reports-refresh-button"
              type="button"
              onClick={loadServers}
              disabled={isLoading || isSubmitting}
            >
              {isLoading ? text.loading : text.refresh}
            </button>
          </div>

          {listError ? <div className="error-banner">{listError}</div> : null}

          <div className="reports-table-wrap">
            <table className="reports-servers-table">
              <thead>
                <tr>
                  <th>{text.type}</th>
                  <th>{text.serverName}</th>
                  <th>{text.ipAddress}</th>
                  <th>{text.port}</th>
                  <th>{text.username}</th>
                  <th>{text.password}</th>
                  <th>{text.status}</th>
                  <th>{text.primary}</th>
                  <th>{text.hierarchy}</th>
                  <th>{text.actions}</th>
                </tr>
              </thead>

              <tbody>
                {servers.length === 0 ? (
                  <tr>
                    <td className="reports-empty-row" colSpan={10}>
                      {isLoading ? text.loadingServers : text.noServers}
                    </td>
                  </tr>
                ) : (
                  servers.map((server) => {
                    const isEditing = editingServerUuid === server.UUID;
                    const currentDraft = isEditing ? editDraft : null;

                    return (
                      <tr key={server.UUID}>
                        <td>
                          {isEditing ? (
                            <select
                              className="search-input reports-inline-input"
                              value={currentDraft.accessLevel}
                              onChange={(event) =>
                                handleEditChange(
                                  "accessLevel",
                                  event.target.value,
                                )
                              }
                            >
                              <option value="audio">audio</option>
                              <option value="video">video</option>
                              <option value="blast_dial">blast-dial</option>
                            </select>
                          ) : (
                            formatAccessLabel(server.accessLevel)
                          )}
                        </td>
                        <td>
                          {isEditing ? (
                            <input
                              className="search-input reports-inline-input"
                              type="text"
                              value={currentDraft.server_name}
                              onChange={(event) =>
                                handleEditChange(
                                  "server_name",
                                  event.target.value,
                                )
                              }
                            />
                          ) : (
                            server.server_name
                          )}
                        </td>
                        <td>
                          {isEditing ? (
                            <input
                              className="search-input reports-inline-input"
                              type="text"
                              value={currentDraft.ip_address}
                              onChange={(event) =>
                                handleEditChange(
                                  "ip_address",
                                  event.target.value,
                                )
                              }
                            />
                          ) : (
                            server.ip_address
                          )}
                        </td>
                        <td>
                          {isEditing ? (
                            <input
                              className="search-input reports-inline-input"
                              type="number"
                              value={currentDraft.port}
                              onChange={(event) =>
                                handleEditChange("port", event.target.value)
                              }
                              min="1"
                              max="65535"
                            />
                          ) : (
                            server.port
                          )}
                        </td>
                        <td>
                          {isEditing ? (
                            <input
                              className="search-input reports-inline-input"
                              type="text"
                              value={currentDraft.username}
                              onChange={(event) =>
                                handleEditChange("username", event.target.value)
                              }
                            />
                          ) : (
                            server.username
                          )}
                        </td>
                        <td>
                          {isEditing ? (
                            <input
                              className="search-input reports-inline-input"
                              type="password"
                              value={currentDraft.password}
                              onChange={(event) =>
                                handleEditChange("password", event.target.value)
                              }
                            />
                          ) : (
                            "********"
                          )}
                        </td>
                        <td>
                          <div className="status-cell">
                            <span className={getStatusDisplay(server).className}>
                              {getStatusDisplay(server).displayText}
                            </span>
                            {!isEditing && (
                              <button
                                className="reports-secondary-button status-test-button"
                                type="button"
                                onClick={() => handleTestConnection(server.UUID)}
                                disabled={isSubmitting}
                                title={text.testConnection}
                              >
                                🔄
                              </button>
                            )}
                          </div>
                        </td>
                        <td>
                          {server.is_primary ? (
                            <span className="reports-primary-badge">{text.primary}</span>
                          ) : (
                            <button
                              className="reports-secondary-button"
                              type="button"
                              onClick={() => handleSetPrimaryServer(server.UUID)}
                              disabled={isSubmitting}
                              title={text.setPrimary}
                            >
                              {text.setPrimary}
                            </button>
                          )}
                        </td>
                        <td>
                          {isEditing ? (
                            <input
                              className="search-input reports-inline-input"
                              type="number"
                              value={currentDraft.hierarchy_order || 0}
                              onChange={(event) =>
                                handleEditChange("hierarchy_order", event.target.value)
                              }
                              min="0"
                              max="99"
                            />
                          ) : (
                            server.hierarchy_order || 0
                          )}
                        </td>
                        <td>
                          <div className="reports-table-actions">
                            {isEditing ? (
                              <>
                                <button
                                  className="search-button reports-table-button"
                                  type="button"
                                  onClick={handleUpdateServer}
                                  disabled={isSubmitting}
                                >
                                  {text.save}
                                </button>
                                <button
                                  className="reports-secondary-button"
                                  type="button"
                                  onClick={cancelEditing}
                                  disabled={isSubmitting}
                                >
                                  {text.cancel}
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  className="reports-secondary-button edit-soft-button"
                                  type="button"
                                  onClick={() => startEditing(server)}
                                  disabled={isSubmitting}
                                >
                                  {text.edit}
                                </button>
                                <button
                                  className="reports-danger-button"
                                  type="button"
                                  onClick={() =>
                                    handleDeleteServer(server.UUID)
                                  }
                                  disabled={isSubmitting}
                                >
                                  {text.delete}
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
