// ============================================================================
// Login Page - דף התחברות
// ============================================================================
// דף הכניסה למשתמשים. מקבל s_id וסיסמה, שולח ל-API.
// בהצלחה - שומר טוקן ב-localStorage ומפנה ל-Dashboard.
// אם יש טוקן קיים - מפנה ישירות ל-Dashboard (כבר מחובר).
// ============================================================================

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { authAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    s_id: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [loading_login, setLoadingLogin] = useState(false);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const resp = await authAPI.protected();
        const roleFromServer = resp.data?.user?.role || null;

        if (resp.status === 200 && roleFromServer) {
          navigate("/dashboard", { replace: true });
        }
      } catch {
        // Not authenticated, stay on login page
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const { login } = useAuth();

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

  if (loading) {
    return <div className="loading-screen">Loading...</div>;
  }

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
