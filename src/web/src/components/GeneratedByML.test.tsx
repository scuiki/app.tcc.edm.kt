import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { GeneratedByML } from './GeneratedByML'

describe('GeneratedByML', () => {
  it('names where the data came from, for the screen reader and on hover', () => {
    render(<GeneratedByML />)
    const mark = screen.getByRole('img', { name: 'Dado estimado por aprendizado de máquina' })
    fireEvent.mouseEnter(mark)
    expect(screen.getByRole('tooltip')).toHaveTextContent(
      'Dado estimado por aprendizado de máquina',
    )
  })
})
