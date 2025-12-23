import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/token': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/create_vectorDB': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/list_vectorDBs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/upload_file': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/delete_vectorDB': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/query': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/warmup': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
