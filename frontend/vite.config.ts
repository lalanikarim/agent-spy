import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables
  const env = loadEnv(mode, process.cwd(), '');
  
  // Parse port numbers with fallbacks
  const backendPort = env.VITE_BACKEND_PORT || '8000';
  const frontendPort = parseInt(env.VITE_FRONTEND_PORT || '3001');

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0', // Listen on all interfaces for container access
      port: frontendPort,
      proxy: {
        '/api': {
          target: `http://agentspy-minimal-backend:${backendPort}`,
          changeOrigin: true,
          secure: false,
        },
        // Also proxy health check endpoint
        '/health': {
          target: `http://agentspy-minimal-backend:${backendPort}`,
          changeOrigin: true,
          secure: false,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: true,
    },
  };
})
