import React from "react";
import { Link, useLocation } from "react-router-dom";
import "./Sidebar.css";

const menuSections = [
  {
    title: "MANAGER",
    items: [{ label: "Dashboard", path: "/dashboard" }],
  },
  {
    title: "MANAGEMENT",
    items: [
      { label: "Users", path: "/users" },
      { label: "Groups", path: "/groups" },
      { label: "Reports", path: "/reports" },
    ],
  },
  {
    title: "MEETINGS",
    items: [
      { label: "Audio Meetings", path: "/audio-meetings" },
      { label: "Video Meetings", path: "/video-meetings" },
      { label: "Blast-dial Meetings", path: "/blast-dial-meetings" },
    ],
  },
  {
    title: "SUPPORT",
    items: [
      { label: "Settings", path: "/settings" },
      { label: "Help", path: "/help" },
    ],
  },
];

export default function Sidebar() {
  const location = useLocation();

  return (
    <aside className="sidebar">
      <div className="sidebar-header">Toolbar</div>
      <nav className="sidebar-nav">
        {menuSections.map((section) => (
          <div className="sidebar-menu-section" key={section.title}>
            <div className="sidebar-section-title">{section.title}</div>

            {section.items.map((item) => (
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
    </aside>
  );
}
