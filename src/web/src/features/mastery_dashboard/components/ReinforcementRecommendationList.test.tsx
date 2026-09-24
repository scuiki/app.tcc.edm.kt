import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ReinforcementRecommendationList } from './ReinforcementRecommendationList'

describe('ReinforcementRecommendationList', () => {
  it('renders each text verbatim, in the backend order', () => {
    render(
      <ReinforcementRecommendationList
        recommendations={[
          { kc_id: 7, kc_name: 'Recursão', mean_mastery: 0.2, text: 'Recursão: primeiro.' },
          { kc_id: 3, kc_name: 'Laços', mean_mastery: 0.35, text: 'Laços: segundo.' },
        ]}
      />,
    )
    expect(screen.getByText('Recomendações de reforço')).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('Recursão: primeiro.')
    expect(items[1]).toHaveTextContent('Laços: segundo.')
  })

  it('shows the untrained empty state for an empty list', () => {
    render(<ReinforcementRecommendationList recommendations={[]} />)
    expect(
      screen.getByText(
        'As recomendações de reforço aparecem após o treino, a partir dos KCs de menor domínio.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryAllByRole('listitem')).toHaveLength(0)
  })
})
