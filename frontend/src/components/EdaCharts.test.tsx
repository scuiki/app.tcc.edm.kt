import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// react-chartjs-2 draws to a <canvas>, which jsdom does not implement. Mock the Bar/Line wrappers
// with marker nodes that echo their chart type — the component contract under test is "renders a
// chart vs. the no-data empty-state per aggregate", not Chart.js's own pixel output (the standard
// jsdom approach). data-testid carries the chart kind so the tests can tell Bar from Line.
vi.mock('react-chartjs-2', () => ({
  Bar: () => <div data-testid="chart-bar" />,
  Line: () => <div data-testid="chart-line" />,
}))

import { EdaCharts } from './EdaCharts'
import type { EdaResponse } from '../api/schema'

// DASH-04: three backend aggregates → success-rate (Bar), learning-curve (Line),
// compile-error-rate (Bar). An empty ({}) aggregate degrades to the eda empty-state for THAT panel,
// never a blank canvas (Pitfall 2). EDA is training-independent — it takes no first_auc/model input.

function eda(overrides: Partial<EdaResponse> = {}): EdaResponse {
  return {
    assignment_id: 1,
    success_rate: {},
    learning_curve: {},
    compile_error_rate: {},
    ...overrides,
  }
}

describe('EdaCharts', () => {
  it('renders a Bar for a non-empty success_rate (not the empty-state)', () => {
    render(<EdaCharts eda={eda({ success_rate: { '439': 0.5 } })} />)
    // The success-rate panel shows a Bar chart; at least one bar marker is present.
    expect(screen.getAllByTestId('chart-bar').length).toBeGreaterThanOrEqual(1)
  })

  it('renders a Line for learning_curve and a Bar for compile_error_rate', () => {
    render(
      <EdaCharts
        eda={eda({
          learning_curve: { '1': 0.4, '2': 0.6 },
          compile_error_rate: { '439': 0.1 },
        })}
      />,
    )
    expect(screen.getByTestId('chart-line')).toBeInTheDocument()
    expect(screen.getAllByTestId('chart-bar').length).toBeGreaterThanOrEqual(1)
  })

  it('renders the eda empty-state (no chart) for an aggregate equal to {}', () => {
    // Only learning_curve has data; success_rate and compile_error_rate are {} → each degrades.
    render(<EdaCharts eda={eda({ learning_curve: { '1': 0.5 } })} />)
    // Two panels are empty → the eda empty-state copy is present, and the only chart is the Line.
    expect(
      screen.getAllByText(
        'Conclua a ingestão de um dataset desta turma para ver taxa de acerto, curvas de aprendizado e erros de compilação.',
      ).length,
    ).toBeGreaterThanOrEqual(1)
    expect(screen.queryByTestId('chart-bar')).not.toBeInTheDocument()
    expect(screen.getByTestId('chart-line')).toBeInTheDocument()
  })

  it('renders without a model/first_auc input (training-independent) — all {} shows no-data, no chart', () => {
    // The prop is just the EDA payload: no first_auc, no version id. All-{} → no-data empty-state.
    render(<EdaCharts eda={eda()} />)
    expect(screen.queryByTestId('chart-bar')).not.toBeInTheDocument()
    expect(screen.queryByTestId('chart-line')).not.toBeInTheDocument()
    expect(
      screen.getAllByText(
        'Conclua a ingestão de um dataset desta turma para ver taxa de acerto, curvas de aprendizado e erros de compilação.',
      ).length,
    ).toBeGreaterThanOrEqual(1)
  })
})
