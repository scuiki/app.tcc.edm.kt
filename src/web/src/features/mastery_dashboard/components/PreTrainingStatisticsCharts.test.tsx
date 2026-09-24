import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// O jsdom não tem canvas, então os gráficos viram marcadores com o tipo
vi.mock('react-chartjs-2', () => ({
  Bar: () => <div data-testid="chart-bar" />,
  Line: () => <div data-testid="chart-line" />,
}))

import type { PreTrainingStatistics } from '../api/usePreTrainingStatistics'
import { PreTrainingStatisticsCharts } from './PreTrainingStatisticsCharts'

const NO_DATA_TEXT =
  'Conclua a ingestão de um dataset desta turma para ver taxa de acerto, curvas de aprendizado e erros de compilação.'

function statistics(overrides: Partial<PreTrainingStatistics> = {}): PreTrainingStatistics {
  return {
    assignment_id: 1,
    success_rate: {},
    learning_curve: {},
    compile_error_rate: {},
    ...overrides,
  }
}

describe('PreTrainingStatisticsCharts', () => {
  it('draws a bar for the success rate', () => {
    render(
      <PreTrainingStatisticsCharts statistics={statistics({ success_rate: { '439': 0.5 } })} />,
    )
    expect(screen.getAllByTestId('chart-bar')).toHaveLength(1)
  })

  it('draws a line for the learning curve and a bar for the compile error rate', () => {
    render(
      <PreTrainingStatisticsCharts
        statistics={statistics({
          learning_curve: { '1': 0.4, '2': 0.6 },
          compile_error_rate: { '439': 0.1 },
        })}
      />,
    )
    expect(screen.getByTestId('chart-line')).toBeInTheDocument()
    expect(screen.getAllByTestId('chart-bar')).toHaveLength(1)
  })

  it('turns each empty series into the empty state instead of a blank chart', () => {
    render(
      <PreTrainingStatisticsCharts statistics={statistics({ learning_curve: { '1': 0.5 } })} />,
    )
    expect(screen.getAllByText(NO_DATA_TEXT)).toHaveLength(2)
    expect(screen.queryByTestId('chart-bar')).not.toBeInTheDocument()
  })
})
