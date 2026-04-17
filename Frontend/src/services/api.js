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

// כתובת הבסיס של ה-API - מ-environment variable או ברירת מחדל
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // מאפשר שליחת cookies (ל-session-based auth אם נדרש בעתיד)
  timeout: 8000, // timeout של 8 שניות — מונע תקיעות כשהבאקנד כבוי
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
    const meetings = await getMockCmsMeetings(type);
    return { data: meetings };
  },
  getMeetingById: async (meetingId) => {
    const meeting = await getMockCmsMeetingById(meetingId);
    return { data: meeting };
  },
  createMeeting: async (meetingData) => {
    const meeting = await createMockCmsMeeting(meetingData);
    return { data: meeting };
  },
  updateMeetingPassword: async (meetingId, newPassword) => {
    const meeting = await updateMockCmsMeetingPassword(meetingId, newPassword);
    return { data: meeting };
  },
  deleteMeeting: async (meetingId, actor) => {
    const result = await deleteMockCmsMeeting(meetingId, actor);
    return { data: result };
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
