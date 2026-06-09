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
import {
  getMockCmsMeetings,
  getMockCmsMeetingById,
  createMockCmsMeeting,
  updateMockCmsMeetingPassword,
  deleteMockCmsMeeting,
} from "../mocks/cmsMeetings";

// כתובת הבסיס של ה-API - undefined יחזור ל-localhost, מחרוזת ריקה תשתמש ב-same-origin
const API_URL = import.meta.env.VITE_API_URL ?? "http://192.168.1.30:8000";
const CMS_MODE = (import.meta.env.VITE_CMS_MODE || "remote").toLowerCase();
const CMS_URL = import.meta.env.VITE_CMS_URL || "";
const CMS_API_KEY = import.meta.env.VITE_CMS_API_KEY || "";

const api = axios.create({
  baseURL: 'http://192.168.30.1:8000'
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
};

// --- CMS API: אינטגרציה עם CMS (כרגע mock מקומי, בעתיד יחליף ל-API אמיתי) ---
export const cmsAPI = {
  getMeetings: async (type) => {
    if (useRemoteCms) {
      return cmsClient.get("/meetings", {
        params: type ? { type } : {},
      });
    }
    const meetings = await getMockCmsMeetings(type);
    return { data: meetings };
  },
  getMeetingById: async (meetingId) => {
    if (useRemoteCms) {
      return cmsClient.get(`/meetings/${meetingId}`);
    }
    const meeting = await getMockCmsMeetingById(meetingId);
    return { data: meeting };
  },
  createMeeting: async (meetingData) => {
    if (useRemoteCms) {
      return cmsClient.post("/meetings", meetingData);
    }
    const meeting = await createMockCmsMeeting(meetingData);
    return { data: meeting };
  },
  updateMeetingPassword: async (meetingId, newPassword) => {
    if (useRemoteCms) {
      return cmsClient.put(`/meetings/${meetingId}/password`, {
        password: newPassword,
      });
    }
    const meeting = await updateMockCmsMeetingPassword(meetingId, newPassword);
    return { data: meeting };
  },
  deleteMeeting: async (meetingId, actor) => {
    if (useRemoteCms) {
      return cmsClient.delete(`/meetings/${meetingId}`, {
        data: { actor },
      });
    }
    const result = await deleteMockCmsMeeting(meetingId, actor);
    return { data: result };
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
      !originalRequest.url.includes("/auth/refresh")
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
