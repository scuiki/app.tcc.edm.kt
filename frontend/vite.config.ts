/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Network bind mirrors the bind rule of the api service (D-02): never bind all-interfaces.
// Default to loopback; override to the tailnet IP (100.96.0.53) via VITE_HOST for Tailscale access.
const host = process.env.VITE_HOST ?? '127.0.0.1'

// Vite validates the Host header and refuses unknown hosts (Pitfall 3). List the Tailscale hostname
// via VITE_ALLOWED_HOSTS (comma-separated) at deploy time; loopback dev needs no entry.
const allowedHosts = (process.env.VITE_ALLOWED_HOSTS ?? '')
  .split(',')
  .map((h) => h.trim())
  .filter(Boolean)

// Same-origin proxy to the internal api service (D-01/D-04). In the compose topology the target is
// the service name `api`, reachable only on the internal network; only the frontend publishes a port.
const apiTarget = process.env.VITE_API_TARGET ?? 'http://api:8099'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host,
    allowedHosts,
    proxy: {
      '/assignments': apiTarget,
      '/mastery-dashboard': apiTarget,
      '/openapi.json': apiTarget,
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: 'src/test/setup.ts',
  },
})
