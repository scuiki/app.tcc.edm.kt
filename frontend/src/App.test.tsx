import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

// react-chartjs-2 draws to <canvas> (unimplemented in jsdom); mock the wrappers with marker nodes,
// same as EdaCharts.test — the App contract under test is wiring/tab-routing, not Chart.js pixels.
vi.mock('react-chartjs-2', () => ({
  Bar: () => <div data-testid="chart-bar" />,
  Line: () => <div data-testid="chart-line" />,
}))

import App from './App'
import {
  assignments,
  edaNoData,
  edaWithData,
  masteryTrained,
  masteryUntrained,
  recommendations,
} from './test/fixtures'
import type { AssignmentsResponse } from './api/schema'

// One fresh client per render so a query cached in one test never leaks into the next; retry off so an
// error fixture resolves to the error copy immediately (mirrors main.tsx).
function renderApp() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>,
  )
}

// Route the global fetch by path to the matching fixture. Per-test overrides cover the empty/error
// states without each test re-stubbing every endpoint.
type FetchOverrides = {
  assignmentsBody?: AssignmentsResponse
  masteryId1?: 'trained' | 'untrained'
  edaId1?: 'data' | 'nodata'
  failMastery?: boolean
}

function stubFetch(overrides: FetchOverrides = {}) {
  const {
    assignmentsBody = assignments,
    masteryId1 = 'trained',
    edaId1 = 'data',
    failMastery = false,
  } = overrides

  const ok = (body: unknown): Response =>
    ({ ok: true, status: 200, json: async () => body }) as Response

  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input: RequestInfo | URL) => {
    const path = typeof input === 'string' ? input : input.toString()

    if (path === '/assignments') return ok(assignmentsBody)

    if (path.startsWith('/dashboard/mastery/')) {
      if (failMastery) return { ok: false, status: 503 } as Response
      const trained = path.endsWith('/1') ? masteryId1 === 'trained' : false
      return ok(trained ? masteryTrained : masteryUntrained)
    }
    if (path.startsWith('/dashboard/eda/')) {
      const hasData = path.endsWith('/1') ? edaId1 === 'data' : false
      return ok(hasData ? edaWithData : edaNoData)
    }
    if (path.startsWith('/dashboard/recommendations/')) return ok(recommendations)

    throw new Error(`unexpected fetch ${path}`)
  })
}

beforeEach(() => {
  stubFetch()
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('App shell', () => {
  it('renders the navy header with the vendored Facens logo and the three tab labels', async () => {
    renderApp()
    expect(screen.getByRole('img', { name: /facens/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Domínio (mastery)' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Análise exploratória' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Recomendações de reforço' })).toBeInTheDocument()
  })

  it('lists assignments from useAssignments in the rail under "Turma / Assignment"', async () => {
    renderApp()
    const rail = await screen.findByRole('navigation', { name: /turma \/ assignment/i })
    // The rail shows Loading until useAssignments resolves; await the rows, then assert both render.
    expect(await within(rail).findByRole('button', { name: /Assignment 439/ })).toBeInTheDocument()
    expect(within(rail).getByRole('button', { name: /Assignment 440/ })).toBeInTheDocument()
  })

  it('selecting a trained assignment shows the mastery tab with the always-visible uncertainty frame', async () => {
    renderApp()
    fireEvent.click(await screen.findByRole('button', { name: /Assignment 439/ }))
    // Mastery is the default tab; the uncertainty frame (role=note) is present with the trained copy.
    const frame = await screen.findByRole('note')
    expect(frame).toHaveTextContent('AUC da turma 76%')
    expect(frame).toHaveTextContent('Não é um veredito.')
  })

  it('shows the uncertainty frame for an UNTRAINED assignment too (untrained copy, no all-red grid)', async () => {
    renderApp()
    fireEvent.click(await screen.findByRole('button', { name: /Assignment 440/ }))
    const frame = await screen.findByRole('note')
    expect(frame).toHaveTextContent(
      'Modelo ainda não treinado para este assignment. A EDA abaixo está disponível mesmo assim.',
    )
  })

  it('switches to the EDA tab and renders charts', async () => {
    renderApp()
    fireEvent.click(await screen.findByRole('button', { name: /Assignment 439/ }))
    fireEvent.click(screen.getByRole('tab', { name: 'Análise exploratória' }))
    await waitFor(() =>
      expect(screen.getAllByTestId('chart-bar').length).toBeGreaterThanOrEqual(1),
    )
  })

  it('switches to the Recomendações tab and shows the verbatim pt-BR text', async () => {
    renderApp()
    fireEvent.click(await screen.findByRole('button', { name: /Assignment 439/ }))
    fireEvent.click(screen.getByRole('tab', { name: 'Recomendações de reforço' }))
    expect(
      await screen.findByText(
        'Laços de repetição: domínio parcial — vale revisar (mastery média 43%).',
      ),
    ).toBeInTheDocument()
  })

  it('shows the no-assignments empty-state when the list is empty', async () => {
    stubFetch({ assignmentsBody: { assignments: [] } })
    renderApp()
    expect(await screen.findByText('Nenhum assignment disponível')).toBeInTheDocument()
  })

  it('shows the error copy when a dashboard query fails', async () => {
    stubFetch({ failMastery: true })
    renderApp()
    fireEvent.click(await screen.findByRole('button', { name: /Assignment 439/ }))
    expect(
      await screen.findByText(
        'Não foi possível carregar os dados do dashboard. Verifique se a API está no ar e tente novamente.',
      ),
    ).toBeInTheDocument()
  })
})
