import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { HeatmapGrid } from './HeatmapGrid'
import type { MasteryCell } from '../api/schema'

// The heatmap only colors backend-authored mastery (D-08); these tests pin the band cutoffs (via the
// non-color cue, not the fill) and the untrained empty-state guard so an empty matrix never reads as a
// zero-mastery verdict (Pitfall 2).

describe('HeatmapGrid', () => {
  it('bands a 0.30 cell as Baixo with a non-color cue carrying the band word + percent', () => {
    const matrix: MasteryCell[] = [{ subject_id: 's1', kc_id: 7, mastery: 0.3 }]
    render(<HeatmapGrid matrix={matrix} firstAuc={0.76} />)
    const cell = screen.getByRole('gridcell')
    expect(cell).toHaveAttribute('aria-label', expect.stringContaining('Baixo'))
    expect(cell).toHaveAttribute('aria-label', expect.stringContaining('30%'))
    expect(cell).toHaveAttribute('title', expect.stringContaining('Baixo'))
  })

  it('bands a 0.70 cell as Médio (boundary inclusive)', () => {
    const matrix: MasteryCell[] = [{ subject_id: 's1', kc_id: 7, mastery: 0.7 }]
    render(<HeatmapGrid matrix={matrix} firstAuc={0.76} />)
    expect(screen.getByRole('gridcell')).toHaveAttribute(
      'aria-label',
      expect.stringContaining('Médio'),
    )
  })

  it('bands a 0.90 cell as Alto', () => {
    const matrix: MasteryCell[] = [{ subject_id: 's1', kc_id: 7, mastery: 0.9 }]
    render(<HeatmapGrid matrix={matrix} firstAuc={0.76} />)
    expect(screen.getByRole('gridcell')).toHaveAttribute(
      'aria-label',
      expect.stringContaining('Alto'),
    )
  })

  it('always renders the legend', () => {
    const matrix: MasteryCell[] = [{ subject_id: 's1', kc_id: 7, mastery: 0.5 }]
    render(<HeatmapGrid matrix={matrix} firstAuc={0.76} />)
    expect(
      screen.getByText('Baixo (<40%) · Médio (40–70%) · Alto (>70%)'),
    ).toBeInTheDocument()
  })

  it('renders the untrained empty-state (no gridcells) for matrix=[] + first_auc=null', () => {
    render(<HeatmapGrid matrix={[]} firstAuc={null} />)
    expect(
      screen.getByText(
        'Sem heatmap de domínio até o treino do Code-DKT concluir. Veja a EDA enquanto isso.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryAllByRole('gridcell')).toHaveLength(0)
  })
})
