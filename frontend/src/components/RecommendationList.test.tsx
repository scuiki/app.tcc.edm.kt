import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { RecommendationList } from './RecommendationList'
import type { Recommendation } from '../api/schema'

// REC-01: the backend pre-renders each suggestion's pt-BR `text`; the SPA displays it VERBATIM
// (character-for-character, never paraphrased or reconstructed client-side) and in backend order
// (weakest-first, already ranked — no client re-sort, D-08). An empty array degrades to the
// recs-untrained empty-state. T-06.1-09: text is JSX (auto-escaped), never dangerouslySetInnerHTML.

describe('RecommendationList', () => {
  it('renders each recommendation text verbatim', () => {
    const recs: Recommendation[] = [
      {
        kc_id: 3,
        kc_name: 'Laços',
        mean_mastery: 0.32,
        text: 'Laços: domínio baixo na turma — priorize reforço (mastery média 32%).',
      },
    ]
    render(<RecommendationList recommendations={recs} />)
    expect(
      screen.getByText(
        'Laços: domínio baixo na turma — priorize reforço (mastery média 32%).',
      ),
    ).toBeInTheDocument()
  })

  it('renders items in the backend array order (no client reorder)', () => {
    const recs: Recommendation[] = [
      { kc_id: 7, kc_name: 'Recursão', mean_mastery: 0.2, text: 'Recursão: primeiro.' },
      { kc_id: 3, kc_name: 'Laços', mean_mastery: 0.35, text: 'Laços: segundo.' },
    ]
    render(<RecommendationList recommendations={recs} />)
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(items[0]).toHaveTextContent('Recursão: primeiro.')
    expect(items[1]).toHaveTextContent('Laços: segundo.')
  })

  it('renders the recs-untrained empty-state for an empty array', () => {
    render(<RecommendationList recommendations={[]} />)
    expect(
      screen.getByText(
        'As recomendações de reforço aparecem após o treino, a partir dos KCs de menor domínio.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryAllByRole('listitem')).toHaveLength(0)
  })

  it('shows the "Recomendações de reforço" heading', () => {
    const recs: Recommendation[] = [
      { kc_id: 3, kc_name: 'Laços', mean_mastery: 0.32, text: 'Laços: reforce.' },
    ]
    render(<RecommendationList recommendations={recs} />)
    expect(screen.getByText('Recomendações de reforço')).toBeInTheDocument()
  })
})
