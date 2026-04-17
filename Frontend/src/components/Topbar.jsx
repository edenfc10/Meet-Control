import React from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";
import "./Topbar.css";

export default function Topbar() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <header className="topbar">
      <div className="topbar-left">
        <span className="topbar-logo">Meet Control</span>
      </div>
      <div className="topbar-right">
        {currentUser?.s_id && (
          <div className="topbar-user">
            <span className="topbar-sid">{currentUser.s_id}</span>
            <span className="topbar-role-badge">
              {currentUser.role?.toUpperCase()}
            </span>
          </div>
        )}
        <button className="topbar-logout" onClick={handleLogout}>
          Sign out
        </button>
      </div>
    </header>
  );
}
