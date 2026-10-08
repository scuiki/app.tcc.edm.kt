import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { FactsLine } from './FactsLine'

describe('FactsLine', () => {
  it('keeps the facts in order, with the comma as text the screen reader reads', () => {
    render(
      <FactsLine
        facts={[
          { content: '10 problemas' },
          { content: '25 conceitos' },
          { content: 'nenhum problema sem conceito' },
        ]}
      />,
    )
    const line = screen.getByText('10 problemas').closest('p')
    expect(line?.textContent).toBe('10 problemas, 25 conceitos, nenhum problema sem conceito')
  })

  it('has no comma with a single fact', () => {
    render(<FactsLine facts={[{ content: '1 problema' }]} />)
    expect(screen.getByText('1 problema').closest('p')?.textContent).toBe('1 problema')
  })

  it('marks only the alert fact, with the icon before the text', () => {
    render(
      <FactsLine
        facts={[{ content: '10 problemas' }, { content: '1 problema sem conceito', alert: true }]}
      />,
    )
    const alert = screen.getByText('1 problema sem conceito').closest('.facts-line__item')
    expect(alert).toHaveClass('facts-line__item--alert')
    expect(alert?.firstElementChild?.tagName.toLowerCase()).toBe('svg')
    expect(alert?.firstElementChild).toHaveAttribute('aria-hidden', 'true')
    const plain = screen.getByText('10 problemas')
    expect(plain).not.toHaveClass('facts-line__item--alert')
    expect(plain.querySelector('svg')).toBeNull()
  })
})
