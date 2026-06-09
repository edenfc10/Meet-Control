// ============================================================================
// AuthContext - ניהול מצב ההתחברות של המשתמש
// ============================================================================
// Context גלובלי שמנהל:
//   - isAuthenticated: האם המשתמש מחובר
//   - userRole: תפקיד המשתמש (super_admin / admin / agent)
//   - currentUser: אובייקט המשתמש המלא מהשרת
//   - loading: האם טוען מצב התחברות
//   - login(token): שומר טוקן ומביא פרטי משתמש
//   - logout(): מנקה טוקן ומאפס מצב
//
// זרימת עבודה:
//   1. בטעינה - בודק אם יש token ב-localStorage
//   2. אם כן - שולח בקשה ל-/protected/me לאימות
//   3. אם תקין - שומר תפקיד ופרטי משתמש
//   4. אם לא תקין - מבצע logout
// ============================================================================

import { createContext, useContext, useState, useEffect } from "react";
import { authAPI } from "../services/api";

const AuthContext = createContext();
const AUTH_STORAGE_KEY = "meet-manager-user";

const normalizeUser = (payload) => {
  const user = payload?.user ?? payload ?? {};
  const rawRole = user?.role ?? "";
  const role = typeof rawRole === "string" ? rawRole : rawRole?.value || "";

  return {
    s_id: user?.s_id || "",
    role,
  };
};

const readCachedUser = () => {
  try {
    const cached = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!cached) {
      return { s_id: "", role: "" };
    }

    return normalizeUser(JSON.parse(cached));
  } catch {
    return { s_id: "", role: "" };
  }
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(readCachedUser);
  const [loading, setLoading] = useState(true);

  const persistUser = (user) => {
    setCurrentUser(user);

    if (user?.s_id) {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
      return;
    }

    localStorage.removeItem(AUTH_STORAGE_KEY);
  };

  // בטעינה — מנסה לשחזר את המשתמש מהשרת דרך ה-cookie הקיים
  useEffect(() => {
    const restore = async () => {
      try {
        const resp = await authAPI.protected();
        const restoredUser = normalizeUser(resp.data);

        if (resp.status === 200 && restoredUser.s_id) {
          persistUser(restoredUser);
        } else {
          persistUser({ s_id: "", role: "" });
        }
      } catch {
        persistUser({ s_id: "", role: "" });
      } finally {
        setLoading(false);
      }
    };
    restore();
  }, []);

  // פונקציית התחברות - שולחת credentials ושומרת פרטי משתמש
  const login = async ({ s_id, password }) => {
    const resp = await authAPI.login({ s_id, password });
    if (resp.status === 200) {
      persistUser(normalizeUser(resp.data));
    }
  };

  // פונקציית התנתקות - מנקה הכל
  const logout = async () => {
    await authAPI.logout();
    persistUser({ s_id: "", role: "" });
  };

  return (
    <AuthContext.Provider value={{ currentUser, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Hook נוח לשימוש ב-context - חייב להיות בתוך AuthProvider
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
};
