import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api/v1/admin': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api\/v1\/admin/, '/api/v1/admin')
      },
      '/api/knowledge_base': {
        target: 'http://localhost:8001'
      },
      '/api/v1': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api\/v1/, '/api/v1')
      },
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '/api')
      },
      '/image': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/image/, '/image')
      },
    }
  }
})
