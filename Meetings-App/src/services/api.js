import axios from 'axios';
import {
  getMockCmsMeetings,
  getMockCmsMeetingById,
  createMockCmsMeeting,
  updateMockCmsMeetingPassword,
  deleteMockCmsMeeting,
} from '../mocks/cmsMeetings';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Auth API
export const authAPI = {
  login: (loginDetails) => api.post('/auth/login', loginDetails),
  protected: () => api.get('/protected/me'),
};

// User API
export const userAPI = {
  getAllUsers: () => api.get('/users/all'),
  getUserByS_id: (s_id) => api.get(`/users/${s_id}`),
  createAgent: (userData) => api.post('/users/create-agent', userData),
  createAdmin: (userData) => api.post('/users/create-admin', userData),
  deleteUser: (userId) => api.delete(`/users/${userId}`),
};

// Mador API
export const madorAPI = {
  createMador: (madorData) => api.post('/madors/create', madorData),
  listMadors: () => api.get('/madors/all'),
  getMador: (madorId) => api.get(`/madors/${madorId}`),
  deleteMador: (madorId) => api.delete(`/madors/${madorId}`),
  updateMador: (madorId, madorData) => api.put(`/madors/${madorId}`, madorData),
  addMember: (madorId, userId) => api.post(`/madors/${madorId}/add-member/${userId}`),
  removeMember: (madorId, userId) => api.post(`/madors/${madorId}/remove-member/${userId}`),
  addMeeting: (madorId, meetingUuid) => api.post(`/madors/${madorId}/add-meeting/${meetingUuid}`),
};

// Meeting API
export const meetingAPI = {
  getAllMeetings: () => api.get('/meetings/all'),
  getMeeting: (meetingUuid) => api.get(`/meetings/${meetingUuid}`),
  getMeetingByNumber: (number) => api.get(`/meetings/number/${number}`),
  createMeeting: (meetingData) => api.post('/meetings/create', meetingData),
  deleteMeeting: (meetingUuid) => api.delete(`/meetings/${meetingUuid}`),
  updateMeeting: (meetingUuid, meetingData) => api.put(`/meetings/${meetingUuid}`, meetingData),
  getMeetingsByMador: (madorUuid) => api.get(`/meetings/mador/${madorUuid}`),
};

// CMS API (mock for frontend integration)
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

export default api;
