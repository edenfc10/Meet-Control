// ============================================================================
// Login Page - דף התחברות
// ============================================================================
// דף הכניסה למשתמשים. מקבל s_id וסיסמה, שולח ל-API.
// בהצלחה - שומר טוקן ב-localStorage ומפנה ל-Dashboard.
// אם יש טוקן קיים - מפנה ישירות ל-Dashboard (כבר מחובר).
// ============================================================================

import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    s_id: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading_login, setLoadingLogin] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const { login, currentUser } = useAuth();

  useEffect(() => {
    if (currentUser?.s_id) {
      navigate("/dashboard", { replace: true });
    }
  }, [currentUser]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoadingLogin(true);

    try {
      await login(formData);

      navigate("/dashboard", { replace: true });
    } catch (err) {
      const errorMessage =
        err.response?.data?.detail ||
        err.message ||
        "Login failed. Please check your connection and credentials.";
      setError(errorMessage);
    } finally {
      setLoadingLogin(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>Meet Control</h1>
        <p className="login-subtitle">Sign in to your account</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="s_id">S_ID</label>
            <input
              type="text"
              id="s_id"
              name="s_id"
              value={formData.s_id}
              onChange={handleChange}
              placeholder="Enter your S_ID"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
            />
          </div>

          <button
            type="submit"
            className="login-button"
            disabled={loading_login}
          >
            {loading_login ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="login-help">Need help? Contact your administrator.</p>
      </div>
    </div>
  );
}
