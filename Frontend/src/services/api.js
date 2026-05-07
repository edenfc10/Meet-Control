// ============================================================================
// API Service - שירות API מרכזי
// ============================================================================
// קובץ זה מרכז את כל קריאות ה-API של האפליקציה.
// משתמש ב-Axios עם interceptor שמוסיף את ה-JWT token לכל בקשה.
//
// מודולי API:
//   - authAPI:    התחברות + בדיקת token (login, protected/me)
//   - userAPI:    ניהול משתמשים (CRUD)
//   - groupAPI:   ניהול מדורים, חברים, ישיבות
//   - meetingAPI: ניהול ישיבות ב-DB
//   - cmsAPI:     אינטגרציה עם CMS (כרגע mock מקומי)
//
// כתובת ה-API נלקחת מ-VITE_API_URL או ברירת מחדל localhost:8000
// ============================================================================

import axios from "axios";

// כתובת הבסיס של ה-API - undefined יחזור ל-localhost, מחרוזת ריקה תשתמש ב-same-origin
const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const CMS_MODE = (import.meta.env.VITE_CMS_MODE || "real").toLowerCase();
const CMS_URL = import.meta.env.VITE_CMS_URL || "";
const CMS_API_KEY = import.meta.env.VITE_CMS_API_KEY || "";

// החלפה אוטומטית בין CMS אמיתי ל-MOCK
const USE_MOCK = CMS_MODE === "mock";
const CMS_BASE_URL = USE_MOCK ? "/cms_mock" : "/meetings";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // מאפשר שליחת cookies (ל-session-based auth אם נדרש בעתיד)
  timeout: 8000, // timeout של 8 שניות — מונע תקיעות כשהבאקנד כבוי
});

const cmsClient = CMS_URL
  ? axios.create({
      baseURL: CMS_URL,
      headers: {
        "Content-Type": "application/json",
        ...(CMS_API_KEY ? { Authorization: `Bearer ${CMS_API_KEY}` } : {}),
      },
      timeout: 8000,
    })
  : null;

const useRemoteCms = CMS_MODE === "remote" && !!cmsClient;

// --- Auth API: התחברות ובדיקת חיבור ---
export const authAPI = {
  login: (loginDetails) => api.post("/auth/login", loginDetails),
  logout: () => api.post("/auth/logout"),
  refresh: () => api.post("/auth/refresh"),
  protected: () => api.get("/protected/me"),
};

// --- User API: ניהול משתמשים (קריאה, יצירה, עריכה, מחיקה) ---
export const userAPI = {
  getAllUsers: () => api.get("/users/all"),
  updateUser: (userUuid, userData) =>
    api.put(`/users/update/${userUuid}`, userData),
  getUserByS_id: (s_id) => api.get(`/users/${s_id}`),
  getUserByUuid: (uuid) => api.get(`/users/uuid/${uuid}`),
  createAgent: (userData) => api.post("/users/create-agent", userData),
  createViewer: (userData) => api.post("/users/create-viewer", userData),
  createAdmin: (userData) => api.post("/users/create-admin", userData),
  deleteUser: (userId) => api.delete(`/users/${userId}`),
};

// --- Group API: ניהול מדורים, חברים וישיבות ---
export const groupAPI = {
  createGroup: (groupData) => api.post("/groups/create", groupData),
  listGroups: () => api.get("/groups/all"),
  getGroup: (groupId) => api.get(`/groups/${groupId}`),
  deleteGroup: (groupId) => api.delete(`/groups/${groupId}`),
  updateGroup: (groupId, groupData) => api.put(`/groups/${groupId}`, groupData),
  getGroupMembers: (groupId) => api.get(`/groups/${groupId}/members`),
  addMember: (groupId, userId, accessLevel) =>
    api.post(`/groups/${groupId}/add-member/${userId}`, null, {
      params: { access_level: accessLevel },
    }),
  removeMember: (groupId, userId) =>
    api.post(`/groups/${groupId}/remove-member/${userId}`),
  removeMemberAccess: (groupId, userId, accessLevel) =>
    api.post(`/groups/${groupId}/remove-member-access/${userId}`, null, {
      params: { access_level: accessLevel },
    }),
  addMeeting: (groupId, meetingUuid) =>
    api.post(`/groups/${groupId}/add-meeting/${meetingUuid}`),
  removeMeeting: (groupId, meetingUuid) =>
    api.post(`/groups/${groupId}/remove-meeting/${meetingUuid}`),
};

// --- Meeting API: ניהול ישיבות ב-DB ---
export const meetingAPI = {
  getAllMeetings: (accessLevel) =>
    api.get("/meetings/all_meetings", {
      params: accessLevel ? { access_level: accessLevel } : {},
    }),
  getMeeting: (meetingUuid) => api.get(`/meetings/${meetingUuid}`),
  getMeetingByNumber: (number) => api.get(`/meetings/number/${number}`),
  createMeeting: (meetingData) =>
    api.post("/meetings/create_meeting", meetingData),
  deleteMeeting: (meetingUuid) => api.delete(`/meetings/${meetingUuid}`),
  updateMeeting: (meetingUuid, meetingData) =>
    api.put(`/meetings/${meetingUuid}`, meetingData),
  updateMeetingByNumber: (number, meetingData) =>
    api.put(`/meetings/number/${number}`, meetingData),
  getMeetingsByGroup: (groupUuid) => api.get(`/meetings/group/${groupUuid}`),
  updateMeetingPassword: (meetingUuid, newPassword) =>
    api.put(`/meetings/password/${meetingUuid}`, { password: newPassword }),
};

export const favoriteAPI = {
  getFavoriteMeetings: () => api.get("/favorites/meetings"),
  addFavoriteMeeting: (meetingUuid) => api.post(`/favorites/meetings/${meetingUuid}`),
  removeFavoriteMeeting: (meetingUuid) => api.delete(`/favorites/meetings/${meetingUuid}`),
};

export const serverAPI = {
  getAllServers: (accessLevel) =>
    api.get("/servers/all", {
      params: accessLevel ? { access_level: accessLevel } : {},
    }),
  createServer: (serverData) => api.post("/servers/", serverData),
  updateServer: (serverUuid, serverData) =>
    api.put(`/servers/${serverUuid}`, serverData),
  deleteServer: (serverUuid) => api.delete(`/servers/${serverUuid}`),
  getPrimaryServer: () => api.get("/servers/primary"),
  setPrimaryServer: (serverUuid) => api.post("/servers/set-primary", { server_uuid: serverUuid }),
  testConnection: (serverUuid) => api.post(`/servers/${serverUuid}/test-connection`),
};

// --- CMS API: אינטגרציה עם Cisco Meeting Server ---
// כעת מתחבר דרך Backend API ל-CMS אמיתי
export const cmsAPI = {
  // ניהול שיחות פעילות
  getActiveCalls: (server = "primary") =>
    api.get(`${CMS_BASE_URL}/calls/active?server_name=${server}`),

  getCallParticipants: (callId, server = "primary") =>
    api.get(`${CMS_BASE_URL}/calls/${callId}/participants?server_name=${server}`),

  getCallDetails: (callId, server = "primary") =>
    api.get(`${CMS_BASE_URL}/calls/${callId}/details?server_name=${server}`),

  getParticipantIds: (callId, server = "primary") =>
    api.get(`${CMS_BASE_URL}/calls/${callId}/participants/ids?server_name=${server}`),

  muteParticipant: (data) =>
    api.post(`${CMS_BASE_URL}/calls/participants/mute`, data),

  kickParticipant: (data) =>
    api.post(`${CMS_BASE_URL}/calls/participants/kick`, data),

  // ניהול CoSpaces (חדרי ועידה)
  getCospaces: (server = "primary") =>
    api.get(`${CMS_BASE_URL}/cospaces?server_name=${server}`),

  getCospaceDetails: (cospaceId, server = "primary") =>
    api.get(`${CMS_BASE_URL}/cospaces/${cospaceId}?server_name=${server}`),

  createCospace: (data) =>
    api.post(`${CMS_BASE_URL}/cospaces`, data),

  deleteCospace: (cospaceId, server = "primary") =>
    api.delete(`${CMS_BASE_URL}/cospaces/${cospaceId}?server_name=${server}`),

  updateCospacePasscode: (cospaceId, password, server = "primary") =>
    api.put(`${CMS_BASE_URL}/cospaces/${cospaceId}/passcode`, {
      passcode: password,
      server_name: server,
    }),

  // פונקציות מערכת
  testCmsConnection: (server = "primary") =>
    api.get(`${CMS_BASE_URL}/cms/status?server_name=${server}`),

  getCmsSystemInfo: (server = "primary") =>
    api.get(`${CMS_BASE_URL}/cms/system?server_name=${server}`),

  // פונקציות legacy לתאימות עם קוד קיים
  getMeetings: async (type) => {
    // ממיר ל-CoSpaces כדי לשמור על תאימות
    const response = await api.get(`${CMS_BASE_URL}/cospaces?server_name=primary`);
    return response;
  },

  getMeeting: async (meetingId) => {
    // ממיר ל-CoSpace details כדי לשמור על תאימות
    return api.get(`${CMS_BASE_URL}/cospaces/${meetingId}?server_name=primary`);
  },

  createMeeting: async (meetingData) => {
    // ממיר ל-CoSpace creation כדי לשמור על תאימות
    return api.post(`${CMS_BASE_URL}/cospaces`, {
      name: meetingData.name,
      uri: meetingData.uri,
      passcode: meetingData.password,
      server_name: "primary",
    });
  },

  updateMeetingPassword: async (meetingId, newPassword) => {
    // ממיר ל-CoSpace passcode update כדי לשמור על תאימות
    return api.put(`${CMS_BASE_URL}/cospaces/${meetingId}/passcode`, {
      passcode: newPassword,
      server_name: "primary",
    });
  },

  deleteMeeting: async (meetingId, actor) => {
    // ממיר ל-CoSpace deletion כדי לשמור על תאימות
    return api.delete(`${CMS_BASE_URL}/cospaces/${meetingId}?server_name=primary`);
  },
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // הגנה: אם אין error.response או error.config, החזר את השגיאה מיד
    if (!error.response || !originalRequest) {
      return Promise.reject(error);
    }

    // אם קיבלנו 401 והבקשה היא לא ל-login ולא ל-refresh (כדי לא לנסות refresh כשאין בכלל session או לולאה אינסופית)
    if (
      error.response.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes("/auth/login") &&
      !originalRequest.url.includes("/auth/refresh")
    ) {
      originalRequest._retry = true;

      try {
        console.log("Received 401, attempting to refresh token...");
        await authAPI.refresh();

        // אם הצלחנו, מריצים מחדש את הבקשה המקורית (העוגיות החדשות יישלחו אוטומטית)
        return api(originalRequest);
      } catch (refreshError) {
        // כאן אפשר להוסיף לוגיקה שמנקה את ה-State של המשתמש ב-Context
        // אל תבצע redirect אם כבר נמצאים ב-/login
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
