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

function logProxy(proxy, options) {
  proxy.on("error", (err, req, res) => {
    console.log("[proxy error]", req.method, req.url, err.message);
  });
  proxy.on("proxyReq", (proxyReq, req, res) => {
    console.log("[proxy req]", req.method, req.url, "->", options.target);
  });
  proxy.on("proxyRes", (proxyRes, req, res) => {
    console.log("[proxy res]", proxyRes.statusCode, req.url);
  });
}

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
    proxy: {
      "/auth": { target: "http://api:8000", changeOrigin: true, configure: logProxy },
      "/users": { target: "http://api:8000", changeOrigin: true, configure: logProxy },
      "/groups": { target: "http://api:8000", changeOrigin: true, configure: logProxy },
      "/meetings": { target: "http://api:8000", changeOrigin: true, configure: logProxy },
      "/favorites": { target: "http://api:8000", changeOrigin: true, configure: logProxy },
      "/servers": { target: "http://api:8000", changeOrigin: true, configure: logProxy },
      "/protected": { target: "http://api:8000", changeOrigin: true, configure: logProxy },
      "/logs": { target: "http://api:8000", changeOrigin: true, configure: logProxy },
    },
  },
});
