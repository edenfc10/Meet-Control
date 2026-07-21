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
  useLocation,
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

import Servers from "./pages/servers";
import Logs from "./pages/Logs";
import Help from "./pages/Help";
import Login from "./pages/Login";

// Assets

import Dashboard from "./pages/Dashboard";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";

const LANGUAGE_STORAGE_KEY = "meet-control-language";

export default function App() {
  const location = useLocation();
  const { loading, currentUser } = useAuth();
  const [language, setLanguage] = useState(
    () => localStorage.getItem(LANGUAGE_STORAGE_KEY) || "en",
  );
  const isLoginRoute = location.pathname === "/login";
  const effectiveLanguage = isLoginRoute ? "en" : language;
  const isRTL = effectiveLanguage === "he";

  useEffect(() => {
    if (!isLoginRoute) {
      localStorage.setItem(LANGUAGE_STORAGE_KEY, language);
    }

    document.documentElement.lang = effectiveLanguage;
    document.documentElement.dir = isRTL ? "rtl" : "ltr";
  }, [language, effectiveLanguage, isRTL, isLoginRoute]);

  const handleToggleLanguage = () => {
    setLanguage((prev) => (prev === "he" ? "en" : "he"));
  };

  if (loading) {
    return (
      <div className="loading-screen">{isRTL ? "טוען..." : "Loading..."}</div>
    );
  }

  if (!currentUser?.s_id && location.pathname !== "/login") {
    return <Navigate to="/login" replace />;
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="*"
        element={
          <div style={{ display: "flex" }}>
            <Sidebar
              language={language}
              onToggleLanguage={handleToggleLanguage}
            />
            <div
              style={{
                flex: 1,
                marginLeft: isRTL ? 0 : 220,
                marginRight: isRTL ? 220 : 0,
                minHeight: "100vh",
                background: "#f4f6fc",
              }}
            >
              <Topbar language={language} />
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
                  <Route
                    path="/"
                    element={
                      ["super_admin", "admin", "agent"].includes(currentUser?.role) ? (
                        <Dashboard language={language} />
                      ) : (
                        <Navigate to="/audio-meetings" replace />
                      )
                    }
                  />
                  <Route
                    path="/dashboard"
                    element={
                      ["super_admin", "admin", "agent"].includes(currentUser?.role) ? (
                        <Dashboard language={language} />
                      ) : (
                        <Navigate to="/audio-meetings" replace />
                      )
                    }
                  />
                  <Route
                    path="/groups"
                    element={<Groups language={language} />}
                  />
                  <Route
                    path="/users"
                    element={
                      ["super_admin", "admin"].includes(currentUser?.role) ? (
                        <Users language={language} />
                      ) : (
                        <Navigate to="/dashboard" replace />
                      )
                    }
                  />
                  <Route
                    path="/reports"
                    element={
                      ["super_admin", "admin"].includes(currentUser?.role) ? (
                        <Reports language={language} />
                      ) : (
                        <Navigate to="/dashboard" replace />
                      )
                    }
                  />

                  <Route
                    path="/audio-meetings"
                    element={
                      currentUser?.role === "admin" && currentUser?.responsible_access_level && currentUser.responsible_access_level !== "audio"
                        ? <Navigate to="/dashboard" replace />
                        : <AudioMeetings language={language} />
                    }
                  />
                  <Route
                    path="/video-meetings"
                    element={
                      currentUser?.role === "admin" && currentUser?.responsible_access_level && currentUser.responsible_access_level !== "video"
                        ? <Navigate to="/dashboard" replace />
                        : <VideoMeetings language={language} />
                    }
                  />
                  <Route
                    path="/blast-dial-meetings"
                    element={<BlastdialMeetings language={language} />}
                  />
                  <Route
                    path="/servers"
                    element={
                      currentUser?.role === "super_admin" ? (
                        <Servers language={language} />
                      ) : (
                        <Navigate to="/dashboard" replace />
                      )
                    }
                  />

                  <Route
                    path="/logs"
                    element={
                      currentUser?.role === "super_admin" ? (
                        <Logs language={language} />
                      ) : (
                        <Navigate to="/dashboard" replace />
                      )
                    }
                  />

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
