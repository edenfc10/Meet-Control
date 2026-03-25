import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: false,
    watch: {
      usePolling: true,
    },
    proxy: {
      '/auth': {
        target: 'http://api:8000',
        changeOrigin: true,
        secure: false,
      },
      '/users': {
        target: 'http://api:8000',
        changeOrigin: true,
        secure: false,
      },
      '/madors': {
        target: 'http://api:8000',
        changeOrigin: true,
        secure: false,
      },
      '/meetings': {
        target: 'http://api:8000',
        changeOrigin: true,
        secure: false,
      },
      '/protected': {
        target: 'http://api:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
