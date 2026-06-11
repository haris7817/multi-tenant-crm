import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev server. The SPA calls the API same-origin at /api/* and Vite proxies to
// the backend, setting the Host header to "<tenant>.crm.local" based on the
// X-Tenant header the client sends. This makes tenant routing work WITHOUT a
// hosts-file entry (browsers can't set Host; a Node proxy can) and avoids CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        // "web" resolves on the Docker compose network; use localhost:8000 if
        // you ever run Vite outside Docker.
        target: "http://web:8000",
        changeOrigin: false,
        configure: (proxy) => {
          proxy.on("proxyReq", (proxyReq, req) => {
            const tenant = req.headers["x-tenant"];
            if (typeof tenant === "string" && tenant) {
              proxyReq.setHeader("Host", `${tenant}.crm.local`);
            }
          });
        },
      },
    },
  },
});
