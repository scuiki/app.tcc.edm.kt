import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Tooltip } from './Tooltip'

describe('Tooltip', () => {
  it('shows the text as soon as the pointer enters, and hides it when it leaves', () => {
    render(
      <Tooltip text="Dado estimado">
        <button type="button" aria-label="Dado estimado">
          x
        </button>
      </Tooltip>,
    )
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()

    fireEvent.mouseEnter(screen.getByRole('button'))
    expect(screen.getByRole('tooltip')).toHaveTextContent('Dado estimado')

    fireEvent.mouseLeave(screen.getByRole('button'))
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('shows the text on keyboard focus too', () => {
    render(
      <Tooltip text="Conceitos">
        <button type="button">c</button>
      </Tooltip>,
    )
    fireEvent.focus(screen.getByRole('button'))
    expect(screen.getByRole('tooltip')).toHaveTextContent('Conceitos')
    fireEvent.blur(screen.getByRole('button'))
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })
})
