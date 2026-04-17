// ============================================================================
// main.jsx - נקודת הכניסה של האפליקציה
// ============================================================================
// מרנדר את אפליקציית React לתוך ה-DOM.
// עוטף את האפליקציה ב:
//   - StrictMode: בדיקות פיתוח נוספות
//   - BrowserRouter: ניתוב URL עם React Router
//   - AuthProvider: ניהול מצב התחברות (טוקן, תפקיד, משתמש)
// ============================================================================

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <App />
      </AuthProvider>
    </BrowserRouter>
  </React.StrictMode>
);
