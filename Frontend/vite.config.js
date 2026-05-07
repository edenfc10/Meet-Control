// ============================================================================
// Vite Configuration - הגדרות שרת הפיתוח
// ============================================================================
// הגדרות עיקריות:
//   - host: 0.0.0.0 (חשוף לכל כתובת - נדרש לעבודה ב-Docker)
//   - port: 5173
//   - usePolling: true (נדרש ל-hot reload ב-Docker/WSL)
//   - proxy: מפנה קריאות API ל-http://api:8000 (שם השירות ב-Docker)
// ============================================================================

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  base: "/",
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    strictPort: false,
    watch: {
      usePolling: true,
    },
  },
});
