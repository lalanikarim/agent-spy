import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig, loadEnv } from "vite";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables
  const env = loadEnv(mode, process.cwd(), "");

  // Parse port numbers with fallbacks
  const backendPort =
    env.PORT ||
    process.env.PORT ||
    env.VITE_BACKEND_PORT ||
    process.env.VITE_BACKEND_PORT ||
    "8000";
  const frontendPort = parseInt(
    env.FRONTEND_PORT ||
      process.env.FRONTEND_PORT ||
      env.VITE_FRONTEND_PORT ||
      process.env.VITE_FRONTEND_PORT ||
      "3000"
  );

  // Determine backend host based on environment
  const backendHost =
    env.HOST ||
    process.env.HOST ||
    env.VITE_BACKEND_HOST ||
    process.env.VITE_BACKEND_HOST ||
    "agentspy-minimal-backend";

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: "0.0.0.0", // Listen on all interfaces for container access
      port: frontendPort,
      // Add comprehensive logging for connection debugging
      hmr: {
        port: 5173,
        host: "0.0.0.0",
      },
      // Log all server events
      onListening: (server: { address: () => unknown }) => {
        const address = server.address();
        console.log("🚀 Vite dev server started!");
        console.log("📍 Server address:", address);
        console.log("🌐 Listening on:", `http://0.0.0.0:${frontendPort}`);
        console.log(
          "🔧 Backend proxy target:",
          `http://${backendHost}:${backendPort}`
        );
        console.log("📋 Environment:", {
          VITE_FRONTEND_PORT: process.env.VITE_FRONTEND_PORT,
          VITE_BACKEND_PORT: process.env.VITE_BACKEND_PORT,
          VITE_BACKEND_HOST: process.env.VITE_BACKEND_HOST,
          NODE_ENV: process.env.NODE_ENV,
        });
      },
      proxy: {
        "/api": {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on("error", (err, _req, _res) => {
              console.log("❌ Proxy error:", err);
            });
            proxy.on("proxyReq", (proxyReq, req, _res) => {
              console.log(
                "🔄 Proxying request:",
                req.method,
                req.url,
                "→",
                proxyReq.getHeader("host")
              );
            });
            proxy.on("proxyRes", (proxyRes, req, _res) => {
              console.log(
                "✅ Proxy response:",
                proxyRes.statusCode,
                req.method,
                req.url
              );
            });
          },
        },
        // Also proxy health check endpoint
        "/health": {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
          secure: false,
        },
        // Proxy WebSocket connections
        "/ws": {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
          secure: false,
          ws: true, // Enable WebSocket proxying
          configure: (proxy, _options) => {
            proxy.on("error", (err, _req, _res) => {
              console.log("❌ WebSocket proxy error:", err);
            });
            // Vite handles WebSocket upgrades; no need to attach an 'upgrade' listener here.
          },
        },
      },
    },
    build: {
      outDir: "dist",
      sourcemap: true,
    },
  };
});
