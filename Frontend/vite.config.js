import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // El backend vive en otro puerto. Se deja explícito aquí para que el
    // origen del navegador coincida con CORS_ALLOWED_ORIGINS del .env de
    // Django — si no coinciden, la cookie de sesión no viaja y el login
    // parece fallar sin decir por qué.
    strictPort: true,
  },
})
