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
    port: 3000,
    allowedHosts, // Read from VITE_ALLOWED_HOSTS in .env
    proxy: {
      // Research API endpoints (separate service on port 8004)
      // IMPORTANT: Must come BEFORE general /api rule to match first
      '/api/research': {
        target: 'http://localhost:8004',
        changeOrigin: true,
      },
      // Python backend API - all /api/* endpoints (structure, etc.)
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      // Python backend API - document endpoints
      '/documents': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      // Python backend API - image endpoints
      '/images': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      // Python backend API - status endpoints
      '/status': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      // Python backend API - health endpoints
      '/health': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      // Python backend API - config endpoints
      '/config': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      // Python backend API - delete endpoint
      '/delete': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      // Python backend API - process endpoint
      '/process': {
        target: 'http://localhost:8002',
        changeOrigin: true,
      },
      // WebSocket for status updates
      '/ws': {
        target: 'ws://localhost:8002',
        ws: true,
        changeOrigin: true,
      },
      // Copyparty uploads
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  }
})
