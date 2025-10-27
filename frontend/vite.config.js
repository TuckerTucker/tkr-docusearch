import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
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
      // Research API endpoints (separate service on port 8004)
      '/api/research': {
        target: 'http://localhost:8004',
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
