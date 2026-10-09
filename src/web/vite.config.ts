/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Nunca em todas as interfaces, o padrão é o loopback e o Tailscale entra por VITE_HOST
const host = process.env.VITE_HOST ?? '127.0.0.1'

// O Vite recusa um Host desconhecido, e o nome do Tailscale entra por VITE_ALLOWED_HOSTS
const allowedHosts = (process.env.VITE_ALLOWED_HOSTS ?? '')
  .split(',')
  .map((h) => h.trim())
  .filter(Boolean)

// A api só é alcançável pelo nome do serviço, e o navegador fala sempre com a própria origem
const apiTarget = process.env.VITE_API_TARGET ?? 'http://api:8099'

export default defineConfig({
  plugins: [react()],
  server: {
    host,
    allowedHosts,
    proxy: {
      '/classrooms': apiTarget,
      '/classroom-imports': apiTarget,
      '/assignments': apiTarget,
      '/knowledge-components': apiTarget,
      '/mastery-dashboard': apiTarget,
      '/training-jobs': apiTarget,
      '/openapi.json': apiTarget,
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: 'src/test/setup.ts',
    // O CSS importado fica vazio nos testes, e só o lido como texto chega inteiro
    css: { include: [/\.css\?raw$/] },
  },
})
