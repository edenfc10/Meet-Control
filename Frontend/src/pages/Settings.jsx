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

const createEmptySection = () => ({
  serverName: "",
  ipAddress: "",
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
  username: server.username,
  password: server.password,
  accessLevel: server.accessLevel,
});

export default function Reports() {
  const { currentUser } = useAuth();
  const isSuperAdmin = currentUser?.role === "super_admin";

  const [settings, setSettings] = useState(createDefaultSettings);
  const [selectedSections, setSelectedSections] = useState(createDefaultSelection);
  const [servers, setServers] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [listError, setListError] = useState("");
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState("");
  const [editingServerUuid, setEditingServerUuid] = useState("");
  const [editDraft, setEditDraft] = useState(null);

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
      setListError(error?.response?.data?.detail || "Failed to load servers.");
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
      setSaveError("Only super_admin can manage servers.");
      setSaveSuccess("");
      return;
    }

    const sectionsToCreate = SETTINGS_SECTIONS.filter(
      (section) => selectedSections[section.key],
    );

    if (sectionsToCreate.length === 0) {
      setSaveError("Mark at least one server section before creating servers.");
      setSaveSuccess("");
      return;
    }

    const incompleteSection = sectionsToCreate.find((section) => {
      const sectionData = settings[section.key];
      return Object.values(sectionData).some((value) => !value.trim());
    });

    if (incompleteSection) {
      setSaveError(`All fields are required for ${incompleteSection.label} server.`);
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
          ? "Server added successfully."
          : `${payloads.length} servers added successfully.`,
      );
      setSaveError("");
    } catch (error) {
      setSaveError(error?.response?.data?.detail || "Failed to add server.");
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
      setSaveError("All fields are required when updating a server.");
      setSaveSuccess("");
      return;
    }

    try {
      setIsSubmitting(true);
      await serverAPI.updateServer(editingServerUuid, {
        server_name: editDraft.server_name.trim(),
        ip_address: editDraft.ip_address.trim(),
        username: editDraft.username.trim(),
        password: editDraft.password,
        accessLevel: editDraft.accessLevel,
      });
      await loadServers();
      cancelEditing();
      setSaveSuccess("Server updated successfully.");
      setSaveError("");
    } catch (error) {
      setSaveError(error?.response?.data?.detail || "Failed to update server.");
      setSaveSuccess("");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteServer = async (serverUuid) => {
    if (!window.confirm("Delete this server?")) {
      return;
    }

    try {
      setIsSubmitting(true);
      await serverAPI.deleteServer(serverUuid);
      await loadServers();
      if (editingServerUuid === serverUuid) {
        cancelEditing();
      }
      setSaveSuccess("Server deleted successfully.");
      setSaveError("");
    } catch (error) {
      setSaveError(error?.response?.data?.detail || "Failed to delete server.");
      setSaveSuccess("");
    } finally {
      setIsSubmitting(false);
    }
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

  return (
    <div className="page">
      <h2 className="page-header">Settings</h2>

      <div className="card">
        <p className="reports-subtitle">
          Manage CMS, video and blast-dial servers from one place.
        </p>

        {!isSuperAdmin ? (
          <div className="error-banner reports-readonly-banner">
            only super_admin can manage server settings.
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
                  <h4 className="reports-section-title" style={{ marginBottom: 0 }}>
                    {section.label}
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
                        toggleSectionSelection(section.key, event.target.checked)
                      }
                      disabled={!isSuperAdmin || isSubmitting}
                    />
                    add
                  </label>
                </div>

                <div className="reports-field-grid">
                  <input
                    className="search-input"
                    type="text"
                    placeholder="server name"
                    value={sectionData.serverName}
                    onChange={(e) =>
                      handleChange(section.key, "serverName", e.target.value)
                    }
                    disabled={!isSuperAdmin}
                  />

                  <input
                    className="search-input"
                    type="text"
                    placeholder="IP address"
                    value={sectionData.ipAddress}
                    onChange={(e) =>
                      handleChange(section.key, "ipAddress", e.target.value)
                    }
                    disabled={!isSuperAdmin}
                  />

                  <input
                    className="search-input"
                    type="text"
                    placeholder="username"
                    value={sectionData.username}
                    onChange={(e) =>
                      handleChange(section.key, "username", e.target.value)
                    }
                    disabled={!isSuperAdmin}
                  />

                  <input
                    className="search-input"
                    type="password"
                    placeholder="password"
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
            {isSubmitting ? "saving..." : "add servers"}
          </button>
        </div>
      </div>

      {isSuperAdmin ? (
        <div className="card reports-servers-card">
          <div className="reports-table-header-row">
            <h3 className="card-title">Servers</h3>
            <button
              className="search-button reports-refresh-button"
              type="button"
              onClick={loadServers}
              disabled={isLoading || isSubmitting}
            >
              {isLoading ? "loading..." : "refresh"}
            </button>
          </div>

          {listError ? <div className="error-banner">{listError}</div> : null}

          <div className="reports-table-wrap">
            <table className="reports-servers-table">
              <thead>
                <tr>
                  <th>type</th>
                  <th>server name</th>
                  <th>IP address</th>
                  <th>username</th>
                  <th>password</th>
                  <th>actions</th>
                </tr>
              </thead>

              <tbody>
                {servers.length === 0 ? (
                  <tr>
                    <td className="reports-empty-row" colSpan={6}>
                      {isLoading
                        ? "Loading servers..."
                        : "No servers found yet."}
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
                            ACCESS_LEVEL_TO_SECTION[server.accessLevel] ||
                            server.accessLevel
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
                          <div className="reports-table-actions">
                            {isEditing ? (
                              <>
                                <button
                                  className="search-button reports-table-button"
                                  type="button"
                                  onClick={handleUpdateServer}
                                  disabled={isSubmitting}
                                >
                                  save
                                </button>
                                <button
                                  className="reports-secondary-button"
                                  type="button"
                                  onClick={cancelEditing}
                                  disabled={isSubmitting}
                                >
                                  cancel
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  className="reports-secondary-button"
                                  type="button"
                                  onClick={() => startEditing(server)}
                                  disabled={isSubmitting}
                                >
                                  edit
                                </button>
                                <button
                                  className="reports-danger-button"
                                  type="button"
                                  onClick={() =>
                                    handleDeleteServer(server.UUID)
                                  }
                                  disabled={isSubmitting}
                                >
                                  delete
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
