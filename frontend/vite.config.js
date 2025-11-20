import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  const env = loadEnv(mode, process.cwd(), '')

  // Parse allowed hosts from environment variable
  const allowedHosts = env.VITE_ALLOWED_HOSTS
    ? env.VITE_ALLOWED_HOSTS.split(',').map(h => h.trim())
    : ['localhost', '127.0.0.1']

  // Centralized service URLs from environment variables
  // See frontend/src/config/urls.js for centralized configuration
  const workerUrl = env.VITE_WORKER_URL || 'http://localhost:8002'
  const researchUrl = env.VITE_RESEARCH_API_URL || 'http://localhost:8004'
  const copypartyUrl = env.VITE_COPYPARTY_URL || 'http://localhost:8000'
  const workerWsUrl = workerUrl.replace(/^http/, 'ws')

  return {
  plugins: [react()],
  build: {
    // Optimize chunks for production
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'query-vendor': ['@tanstack/react-query'],
          'markdown-vendor': ['react-markdown'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  server: {
    host: '0.0.0.0', // Listen on all network interfaces
    port: parseInt(env.VITE_FRONTEND_PORT) || 42007,
    allowedHosts, // Read from VITE_ALLOWED_HOSTS in .env
    proxy: {
      // Research API endpoints (separate service on port 8004)
      // IMPORTANT: Must come BEFORE general /api rule to match first
      '/api/research': {
        target: researchUrl,
        changeOrigin: true,
      },
      // Python backend API - all /api/* endpoints (structure, etc.)
      '/api': {
        target: workerUrl,
        changeOrigin: true,
      },
      // Python backend API - document endpoints
      '/documents': {
        target: workerUrl,
        changeOrigin: true,
      },
      // Python backend API - image endpoints
      '/images': {
        target: workerUrl,
        changeOrigin: true,
      },
      // Python backend API - status endpoints
      '/status': {
        target: workerUrl,
        changeOrigin: true,
      },
      // Python backend API - health endpoints
      '/health': {
        target: workerUrl,
        changeOrigin: true,
      },
      // Python backend API - config endpoints
      '/config': {
        target: workerUrl,
        changeOrigin: true,
      },
      // Python backend API - delete endpoint
      '/delete': {
        target: workerUrl,
        changeOrigin: true,
      },
      // Python backend API - process endpoint
      '/process': {
        target: workerUrl,
        changeOrigin: true,
      },
      // WebSocket for status updates
      '/ws': {
        target: workerWsUrl,
        ws: true,
        changeOrigin: true,
      },
      // Copyparty uploads
      '/uploads': {
        target: copypartyUrl,
        changeOrigin: true,
      },
    },
  },
  }
})
