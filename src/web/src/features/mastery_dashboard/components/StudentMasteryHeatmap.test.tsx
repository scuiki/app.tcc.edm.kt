import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { StudentMasteryHeatmap } from './StudentMasteryHeatmap'

function renderOneCell(mastery: number) {
  render(
    <StudentMasteryHeatmap
      matrix={[{ student_id: 's1', kc_id: 7, mastery }]}
      firstAttemptAuc={0.76}
    />,
  )
  return screen.getByRole('gridcell')
}

describe('StudentMasteryHeatmap', () => {
  it('labels a 0.30 cell as Baixo, with the word and the percent', () => {
    const cell = renderOneCell(0.3)
    expect(cell).toHaveAttribute('aria-label', 'Baixo 30%')
    expect(cell).toHaveAttribute('title', 'Baixo 30%')
  })

  it('labels a 0.70 cell as Médio, the upper edge being inclusive', () => {
    expect(renderOneCell(0.7)).toHaveAttribute('aria-label', 'Médio 70%')
  })

  it('labels a 0.90 cell as Alto', () => {
    expect(renderOneCell(0.9)).toHaveAttribute('aria-label', 'Alto 90%')
  })

  it('always renders the legend', () => {
    renderOneCell(0.5)
    expect(screen.getByText('Baixo (<40%) · Médio (40–70%) · Alto (>70%)')).toBeInTheDocument()
  })

  it('shows the untrained empty state, with no cells, without a model', () => {
    render(<StudentMasteryHeatmap matrix={[]} firstAttemptAuc={null} />)
    expect(
      screen.getByText(
        'Sem heatmap de domínio até o treino do Code-DKT concluir. Veja a EDA enquanto isso.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryAllByRole('gridcell')).toHaveLength(0)
  })
})
