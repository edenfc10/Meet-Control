import { Routes, Route, NavLink, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import "./App.css";

// Pages
import Madors from "./pages/Madors";
import Users from "./pages/Users";
import Reports from "./pages/Reports";
import AudioMeetings from "./pages/AudioMeetings";
import BlastdialMeetings from "./pages/BlastdialMeetings";
import VideoMeetings from "./pages/VideoMeetings";
import Profile from "./pages/Profile";
import Settings from "./pages/Settings";
import Help from "./pages/Help";
import Login from "./pages/Login";

// Components
import ProtectedRoute from "./components/ProtectedRoute";

// Assets
import Dashboard from "./pages/Dashboard";
import appLogo from "./assets/applogo.svg";
import dashboardIcon from "./assets/icons/dashboard.svg";
import groupsIcon from "./assets/icons/groups.svg";
import reportsIcon from "./assets/icons/reports.svg";
import audioIcon from "./assets/icons/audio-meetings.svg";
import blastdialIcon from "./assets/icons/blastdial-meetings.svg";
import videoIcon from "./assets/icons/video-meetings.svg";
import profileIcon from "./assets/icons/profile.svg";
import settingsIcon from "./assets/icons/settings.svg";
import helpIcon from "./assets/icons/help.svg";

// Main Layout Component
function MainLayout() {
  const navigate = useNavigate();
  const { logout, userRole, currentUser } = useAuth();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <img src={appLogo} alt="App Logo" className="app-logo" />
          <div className="header-title">Meet Manager</div>
        </div>
        <div className="header-actions">
          <div className="header-user-panel" title={`Connected as ${userRole || "unknown"}`}>
            <span className="header-user-name">{currentUser?.username || "User"}</span>
            <span className={`header-role-badge role-${userRole || "agent"}`}>
              {userRole || "unknown"}
            </span>
          </div>
          <button className="profile-button" onClick={handleLogout} title="Sign out">
            Sign out
          </button>
        </div>
      </header>

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-section">
          <div className="sidebar-section-title">Job Manager</div>
          <NavLink to="/dashboard">
            <img src={dashboardIcon} className="nav-icon" alt="Dashboard" />
            Dashboard
          </NavLink>
          <NavLink to="/madors">
            <img src={groupsIcon} className="nav-icon" alt="Madors" />
            Madors
          </NavLink>
          <NavLink to="/users">
            <img src={profileIcon} className="nav-icon" alt="Users" />
            Users
          </NavLink>
          <NavLink to="/reports">
            <img src={reportsIcon} className="nav-icon" alt="Reports" />
            Reports
          </NavLink>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-title">Meetings</div>
          <NavLink to="/audio">
            <img src={audioIcon} className="nav-icon" alt="Audio Meetings" />
            Audio Meetings
          </NavLink>
          <NavLink to="/blastdial">
            <img src={blastdialIcon} className="nav-icon" alt="Blastdial Meetings" />
            Blastdial Meetings
          </NavLink>
          <NavLink to="/video">
            <img src={videoIcon} className="nav-icon" alt="Video Meetings" />
            Video Meetings
          </NavLink>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-title">Preferences</div>
          <NavLink to="/profile">
            <img src={profileIcon} className="nav-icon" alt="Profile" />
            Profile
          </NavLink>
          <NavLink to="/settings">
            <img src={settingsIcon} className="nav-icon" alt="Settings" />
            Settings
          </NavLink>
          <NavLink to="/help">
            <img src={helpIcon} className="nav-icon" alt="Help" />
            Help
          </NavLink>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/madors" element={<Madors />} />
          <Route path="/groups" element={<Navigate to="/madors" replace />} />
          <Route path="/users" element={<Users />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/audio" element={<AudioMeetings />} />
          <Route path="/blastdial" element={<BlastdialMeetings />} />
          <Route path="/video" element={<VideoMeetings />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/help" element={<Help />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  const { loading } = useAuth();

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
