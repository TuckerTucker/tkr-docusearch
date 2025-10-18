import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
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
      // Research API endpoints (if mounted)
      '/api/research': {
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
})
