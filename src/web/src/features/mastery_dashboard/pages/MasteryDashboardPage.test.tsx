import { fireEvent, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

// O jsdom não tem canvas, então os gráficos viram marcadores
vi.mock('react-chartjs-2', () => ({
  Bar: () => <div data-testid="chart-bar" />,
  Line: () => <div data-testid="chart-line" />,
}))

import { jsonResponse, renderWithClient } from '../../../test/renderWithClient'
import {
  assignments,
  masteryTrained,
  masteryUntrained,
  recommendations,
  statisticsWithData,
  statisticsWithoutData,
} from '../testFixtures'
import { MasteryDashboardPage } from './MasteryDashboardPage'

interface Overrides {
  assignmentsBody?: unknown
  failMastery?: boolean
}

// Cada rota da api responde com a fixture do seu estado
function stubApi({ assignmentsBody = assignments, failMastery = false }: Overrides = {}) {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const path = String(input)
    if (path === '/assignments') return jsonResponse(assignmentsBody)
    if (path.endsWith('/mastery')) {
      if (failMastery) return jsonResponse({}, 503)
      return jsonResponse(path.includes('/1/') ? masteryTrained : masteryUntrained)
    }
    if (path.endsWith('/pre-training-statistics')) {
      return jsonResponse(path.includes('/1/') ? statisticsWithData : statisticsWithoutData)
    }
    if (path.endsWith('/recommendations')) return jsonResponse(recommendations)
    throw new Error(`fetch inesperado ${path}`)
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

async function selectAssignment(name: RegExp) {
  fireEvent.click(await screen.findByRole('button', { name }))
}

describe('MasteryDashboardPage', () => {
  it('lists the assignments in the rail', async () => {
    stubApi()
    renderWithClient(<MasteryDashboardPage />)
    const rail = screen.getByRole('navigation', { name: 'Turma / Assignment' })
    expect(await within(rail).findByRole('button', { name: 'Assignment 439' })).toBeInTheDocument()
    expect(within(rail).getByRole('button', { name: 'Assignment 440' })).toBeInTheDocument()
  })

  it('asks for a pick while nothing is selected, without claiming the list is empty', async () => {
    stubApi()
    renderWithClient(<MasteryDashboardPage />)
    expect(await screen.findByText('Selecione um assignment')).toBeInTheDocument()
    expect(screen.queryByText('Nenhum assignment disponível')).not.toBeInTheDocument()
  })

  it('shows the empty state when there is no assignment', async () => {
    stubApi({ assignmentsBody: { assignments: [] } })
    renderWithClient(<MasteryDashboardPage />)
    expect(await screen.findByText('Nenhum assignment disponível')).toBeInTheDocument()
  })

  it('shows the trained model note on the mastery tab', async () => {
    stubApi()
    renderWithClient(<MasteryDashboardPage />)
    await selectAssignment(/Assignment 439/)
    const note = await screen.findByRole('note')
    expect(note).toHaveTextContent('AUC da turma 76%')
  })

  it('shows the note for an untrained assignment too', async () => {
    stubApi()
    renderWithClient(<MasteryDashboardPage />)
    await selectAssignment(/Assignment 440/)
    expect(await screen.findByRole('note')).toHaveTextContent('Modelo ainda não treinado')
  })

  it('switches to the pre-training statistics tab and draws the charts', async () => {
    stubApi()
    renderWithClient(<MasteryDashboardPage />)
    await selectAssignment(/Assignment 439/)
    fireEvent.click(screen.getByRole('tab', { name: 'Análise exploratória' }))
    expect(await screen.findAllByTestId('chart-bar')).toHaveLength(2)
  })

  it('switches to the recommendations tab and shows the text verbatim', async () => {
    stubApi()
    renderWithClient(<MasteryDashboardPage />)
    await selectAssignment(/Assignment 439/)
    fireEvent.click(screen.getByRole('tab', { name: 'Recomendações de reforço' }))
    expect(
      await screen.findByText(
        'Laços de repetição: domínio parcial — vale revisar (mastery média 43%).',
      ),
    ).toBeInTheDocument()
  })

  it('shows the error when a dashboard request fails', async () => {
    stubApi({ failMastery: true })
    renderWithClient(<MasteryDashboardPage />)
    await selectAssignment(/Assignment 439/)
    expect(
      await screen.findByText(
        'Não foi possível carregar os dados do dashboard. Verifique se a API está no ar e tente novamente.',
      ),
    ).toBeInTheDocument()
  })
})
