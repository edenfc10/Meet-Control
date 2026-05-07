import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Sidebar.css";

const getMenuSections = (isHebrew) => [
  {
    title: isHebrew ? "ראשי" : "MANAGER",
    items: [{ label: isHebrew ? "לוח צג" : "Dashboard", path: "/dashboard" }],
  },
  {
    title: isHebrew ? "ניהול מערכת" : "MANAGEMENT",
    items: [
      { label: isHebrew ? "משתמשים" : "Users", path: "/users" },
      { label: isHebrew ? "מדורים" : "Groups", path: "/groups" },
      { label: isHebrew ? "דוחות" : "Reports", path: "/reports" },
    ],
  },
  {
    title: isHebrew ? "ועידות" : "MEETINGS",
    items: [
      {
        label: isHebrew ? "ישיבות אודיו" : "Audio Meetings",
        path: "/audio-meetings",
      },
      {
        label: isHebrew ? "ישיבות וידאו" : "Video Meetings",
        path: "/video-meetings",
      },
      {
        label: isHebrew ? "ישיבות הזנקה" : "Blast-dial Meetings",
        path: "/blast-dial-meetings",
      },
    ],
  },
  {
    title: isHebrew ? "תמיכה" : "SUPPORT",
    items: [
      { label: isHebrew ? "הגדרות" : "Settings", path: "/settings" },
      { label: isHebrew ? "עזרה" : "Help", path: "/help" },
    ],
  },
];

export default function Sidebar({ language = "en", onToggleLanguage }) {
  const location = useLocation();
  const { currentUser } = useAuth();
  const isHebrew = language === "he";
  const menuSections = getMenuSections(isHebrew);
  const isSuperAdmin = currentUser?.role === "super_admin";
  const isAdmin = ["super_admin", "admin"].includes(currentUser?.role);

  return (
    <aside className="sidebar">
      <nav className="sidebar-nav">
        {menuSections.map((section) => (
          <div className="sidebar-menu-section" key={section.title}>
            <div className="sidebar-section-title">{section.title}</div>

            {section.items
              .filter((item) => {
                if (item.path === "/settings") return isSuperAdmin;
                if (item.path === "/reports") return isAdmin;
                return true;
              })
              .map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={
                    location.pathname === item.path
                      ? "sidebar-link active"
                      : "sidebar-link"
                  }
                >
                  {item.label}
                </Link>
              ))}
          </div>
        ))}
      </nav>
      <div className="sidebar-footer">
        <button
          type="button"
          className="sidebar-language-btn"
          aria-label={isHebrew ? "Switch to English" : "Switch to Hebrew"}
          onClick={onToggleLanguage}
        >
          <span className="sidebar-language-icon" aria-hidden="true">
            🌐
          </span>
          <span>{isHebrew ? "English" : "עברית"}</span>
        </button>
        <div className="sidebar-product">© A Product of Avnet</div>
      </div>
    </aside>
  );
}
