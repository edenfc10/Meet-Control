// ============================================================================
// App.jsx - קומפוננטת האפליקציה הראשית
// ============================================================================
// מכילה את:
//   - MainLayout: התפריט הראשי (Header + Sidebar + Routes)
//   - Sidebar: ניווט צדדי עם קישורים לכל הדפים
//   - Routes: ניתוב כל הדפים (מוגנים ב-ProtectedRoute)
//
// מבנה הדפים:
//   /login      - דף התחברות (ללא הגנה)
//   /dashboard  - דף ראשי
//   /groups     - ניהול קבוצות
//   /users      - ניהול משתמשים
//   /reports    - דוחות
//   /audio      - ישיבות אודיו
//   /video      - ישיבות וידאו
//   /blastdial  - ישיבות Blastdial
//   /profile, /settings, /help - דפי העדפות
// ============================================================================

import { useEffect, useMemo, useState } from "react";
import {
  Routes,
  Route,
  NavLink,
  Navigate,
  useNavigate,
} from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { groupAPI } from "./services/api";
import "./App.css";

// Pages
import Groups from "./pages/Groups";
import Users from "./pages/Users";
import Reports from "./pages/Reports";
import AudioMeetings from "./pages/AudioMeetings";
import VideoMeetings from "./pages/VideoMeetings";
import BlastdialMeetings from "./pages/BlastdialMeetings";

import Settings from "./pages/Settings";
import Help from "./pages/Help";
import Login from "./pages/Login";

// Assets

import Dashboard from "./pages/Dashboard";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

export default function App() {
  const { loading } = useAuth();

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="*"
        element={
          <div style={{ display: "flex" }}>
            <Sidebar />
            <div
              style={{
                flex: 1,
                marginLeft: 220,
                minHeight: "100vh",
                background: "#f4f6fc",
              }}
            >
              <Topbar />
              <div
                style={{
                  paddingTop: 60,
                  paddingLeft: 20,
                  paddingRight: 20,
                  paddingBottom: 20,
                  boxSizing: "border-box",
                }}
              >
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/dashboard" element={<Dashboard />} />
                  <Route path="/groups" element={<Groups />} />
                  <Route path="/users" element={<Users />} />
                  <Route path="/reports" element={<Reports />} />
                  <Route path="/audio-meetings" element={<AudioMeetings />} />
                  <Route path="/video-meetings" element={<VideoMeetings />} />
                  <Route
                    path="/blast-dial-meetings"
                    element={<BlastdialMeetings />}
                  />
                  <Route path="/settings" element={<Settings />} />
                  <Route path="/help" element={<Help />} />
                </Routes>
              </div>
            </div>
          </div>
        }
      />
    </Routes>
  );
}
