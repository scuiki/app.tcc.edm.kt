import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './styles/tokens.css'
import App from './App.tsx'

// One QueryClient for the whole app; a single provider wraps App so every hook shares the cache
// (Pattern 2). No retries on the dashboard reads — a down api should surface the error copy promptly
// rather than stall behind silent retries.
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
