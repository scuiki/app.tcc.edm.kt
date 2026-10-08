import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { GeneratedByLLM } from './GeneratedByLLM'

describe('GeneratedByLLM', () => {
  it('names where the text came from, for the screen reader and on hover', () => {
    render(<GeneratedByLLM />)
    const mark = screen.getByRole('img', { name: 'Gerado pelo modelo de linguagem' })
    fireEvent.mouseEnter(mark)
    expect(screen.getByRole('tooltip')).toHaveTextContent('Gerado pelo modelo de linguagem')
  })

  it('takes the size of the end of a text when no place is given', () => {
    render(<GeneratedByLLM />)
    expect(screen.getByRole('img')).toHaveClass('generated-by-llm', 'generated-by-llm--text')
  })

  it.each([
    ['text', 14],
    ['title', 16],
    ['label', 12],
    ['tab', 10],
  ] as const)(
    'keeps the name and the hint in the %s place, with the size of that place',
    (variant, iconSize) => {
      render(<GeneratedByLLM variant={variant} />)
      const mark = screen.getByRole('img', { name: 'Gerado pelo modelo de linguagem' })
      expect(mark).toHaveClass('generated-by-llm', `generated-by-llm--${variant}`)
      expect(mark.querySelector('svg')).toHaveAttribute('width', String(iconSize))
      fireEvent.mouseEnter(mark)
      expect(screen.getByRole('tooltip')).toHaveTextContent('Gerado pelo modelo de linguagem')
    },
  )
})
