import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { UncertaintyFrame } from './UncertaintyFrame'

// DASH-05: the frame is ALWAYS visible (never suppressed, never a bare number) and carries verbatim
// pt-BR copy that differs between trained and untrained states.

describe('UncertaintyFrame', () => {
  it('renders the trained copy with AUC via formatPercent and the trained_at slot', () => {
    render(<UncertaintyFrame firstAuc={0.76} trainedAt="2026-06-21T00:00:00Z" />)
    const frame = screen.getByRole('note')
    expect(frame).toHaveTextContent('AUC da turma 76%')
    expect(frame).toHaveTextContent('Não é um veredito.')
    expect(frame).toHaveTextContent('2026-06-21T00:00:00Z')
  })

  it('renders the untrained copy when first_auc is null', () => {
    render(<UncertaintyFrame firstAuc={null} trainedAt={null} />)
    expect(
      screen.getByText(
        'Modelo ainda não treinado para este assignment. A EDA abaixo está disponível mesmo assim.',
      ),
    ).toBeInTheDocument()
  })

  it('always renders a non-null frame element in both states', () => {
    const { rerender } = render(
      <UncertaintyFrame firstAuc={0.76} trainedAt="2026-06-21T00:00:00Z" />,
    )
    expect(screen.getByRole('note')).not.toBeNull()
    rerender(<UncertaintyFrame firstAuc={null} trainedAt={null} />)
    expect(screen.getByRole('note')).not.toBeNull()
  })
})
