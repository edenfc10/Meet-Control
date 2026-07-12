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

const api = axios.create({
  baseURL: '', // proxy via Vite: /auth, /users etc. → http://api:8000 (same-origin, cookies work)
  withCredentials: true,
});

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
  addMeeting: (groupId, meetingUuid, accessLevel) =>
    api.post(`/groups/${groupId}/add-meeting/${meetingUuid}`, null, {
      params: accessLevel ? { access_level: accessLevel } : {},
    }),
  removeMeeting: (groupId, meetingUuid, accessLevel) =>
    api.post(`/groups/${groupId}/remove-meeting/${meetingUuid}`, null, {
      params: accessLevel ? { access_level: accessLevel } : {},
    }),
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
  deleteMeeting: (meetingUuid, accessLevel) => api.delete(`/meetings/${meetingUuid}`, {
      params: accessLevel ? { access_level: accessLevel } : {},
    }),
  updateMeeting: (meetingUuid, meetingData) =>
    api.put(`/meetings/${meetingUuid}`, meetingData),
  updateMeetingByNumber: (number, meetingData) =>
    api.put(`/meetings/number/${number}`, meetingData),
  getMeetingsByGroup: (groupUuid) => api.get(`/meetings/group/${groupUuid}`),
  updateMeetingPassword: (meetingNumber, newPassword, accessLevel) =>
    api.put(`/meetings/password/${meetingNumber}`, { password: newPassword }, {
      params: accessLevel ? { access_level: accessLevel } : {},
    }),
  updateMeetingName: (meetingNumber, newName, accessLevel) =>
    api.put(`/meetings/name/${meetingNumber}`, { name: newName }, {
      params: accessLevel ? { access_level: accessLevel } : {},
    }),
  getParticipants: (meetingUuid) => api.get(`/meetings/${meetingUuid}/participants`),
  getLiveParticipants: (meetingUuid) => api.get(`/meetings/${meetingUuid}/live-participants`),
  getLiveStatus: () => api.get("/meetings/live-status"),
  muteParticipant: (meetingUuid, callId, legId, mute) =>
    api.post(`/meetings/${meetingUuid}/mute`, { call_id: callId, leg_id: legId, mute }),
  kickParticipant: (meetingUuid, callId, legId) =>
    api.post(`/meetings/${meetingUuid}/kick`, { call_id: callId, leg_id: legId }),
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
};

export const reportsAPI = {
  getCdrByPhone: (phone) => api.get("/reports/cdr", { params: { phone } }),
};

export const logsAPI = {
  getDates: () => api.get("/logs/dates"),
  getLogByDateAndType: (date, type) => api.get(`/logs/${date}/${type}`),
  downloadLog: (date) => {
    window.location.href = `/logs/${date}/download`;
  },
  downloadAllLogs: () => {
    window.location.href = "/logs/download-all";
  },
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // --- טיפול קריטי בשגיאות רשת / CORS או שרת כבוי ---
    if (!error.response) {
      console.error("Network Error or CORS issue detected.", error);
      // אם הגענו לכאן, אנחנו מניחים שהשרת דחה אותנו (כנראה 401 שמוסתר ע"י CORS)
      // או שהשרת למטה. בשני המקרים - מנקים וזורקים ללוגין (אם לא בלוגין כבר).
      if (originalRequest && !originalRequest.url.includes("/auth/login")) {
         console.warn("Forcing logout due to Network/CORS error on a protected route.");
         handleAuthFailure();
      }
      return Promise.reject(error);
    }

    // --- טיפול בשגיאת 401 Unauthorized ברורה ---
    if (
      error.response.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes("/auth/login") &&
      !originalRequest.url.includes("/auth/refresh") &&
      !originalRequest.url.includes("/auth/logout") &&
      !originalRequest.url.includes("/protected/me")
    ) {
      originalRequest._retry = true;

      try {
        console.log("Received 401, attempting to refresh token...");
        await authAPI.refresh();
        return api(originalRequest);
      } catch (refreshError) {
        console.error("Refresh token failed, redirecting to login...");
        handleAuthFailure();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

function handleAuthFailure() {
  localStorage.removeItem("token"); 
  sessionStorage.clear();
  if (window.location.pathname !== "/login" && window.location.pathname !== "/") {
      // ביצוע רידיירקט אמיתי
      window.location.href = "/login";
  }
}export default api;
