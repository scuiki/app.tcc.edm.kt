import { act, fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Dialog } from './Dialog'
import { Tooltip } from './Tooltip'

// O elemento com 10px de largura a partir da posição dada, para o balão encostar num limite lateral
function placedAt(element: HTMLElement, left: number) {
  const rect = {
    left,
    top: 10,
    width: 10,
    height: 10,
    right: left + 10,
    bottom: 20,
    x: left,
    y: 10,
  }
  element.getBoundingClientRect = () => ({ ...rect, toJSON: () => rect })
  return element
}

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
    act(() => screen.getByRole('button').focus())
    expect(screen.getByRole('tooltip')).toHaveTextContent('Conceitos')
    act(() => screen.getByRole('button').blur())
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('stays hidden on a focus without the visible ring, as when a dialog focuses its first control', () => {
    render(
      <Tooltip text="Domínio é a chance estimada">
        <button type="button">?</button>
      </Tooltip>,
    )
    fireEvent.focus(screen.getByRole('button'))
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
  })

  it('is born in the body outside a dialog', () => {
    render(
      <Tooltip text="Conceitos">
        <button type="button">c</button>
      </Tooltip>,
    )
    fireEvent.mouseEnter(screen.getByRole('button'))
    expect(screen.getByRole('tooltip').parentElement).toBe(document.body)
  })

  it('is born inside the open dialog, so the modal never covers it', () => {
    render(
      <Dialog open onClose={() => {}} title="Aluno 14316">
        <Tooltip text="Dado estimado">
          <button type="button">x</button>
        </Tooltip>
      </Dialog>,
    )
    fireEvent.mouseEnter(screen.getByRole('button', { name: 'x' }))
    expect(screen.getByRole('dialog')).toContainElement(screen.getByRole('tooltip'))
  })

  it.each([
    ['default', 130],
    ['wide', 180],
  ] as const)(
    'stays within both side limits by half of its own width in the %s size',
    (size, halfWidth) => {
      render(
        <Tooltip text="Enunciado do problema" size={size}>
          <button type="button">3</button>
        </Tooltip>,
      )
      const button = screen.getByRole('button')
      fireEvent.mouseEnter(placedAt(button, 0))
      expect(screen.getByRole('tooltip')).toHaveStyle({ left: `${halfWidth}px` })
      fireEvent.mouseLeave(button)

      fireEvent.mouseEnter(placedAt(button, window.innerWidth - 10))
      expect(screen.getByRole('tooltip')).toHaveStyle({
        left: `${window.innerWidth - halfWidth}px`,
      })
    },
  )

  it('takes the wide class only in the wide size', () => {
    render(
      <>
        <Tooltip text="Conceitos">
          <button type="button">comum</button>
        </Tooltip>
        <Tooltip text="Enunciado do problema" size="wide">
          <button type="button">largo</button>
        </Tooltip>
      </>,
    )
    fireEvent.mouseEnter(screen.getByRole('button', { name: 'comum' }))
    expect(screen.getByRole('tooltip')).not.toHaveClass('tooltip--wide')
    fireEvent.mouseLeave(screen.getByRole('button', { name: 'comum' }))

    fireEvent.mouseEnter(screen.getByRole('button', { name: 'largo' }))
    expect(screen.getByRole('tooltip')).toHaveClass('tooltip', 'tooltip--wide')
  })

  it('puts the title before the text and passes the text with the blank line between the paragraphs', () => {
    render(
      <Tooltip title="Problema 3 sem conceito" text={'Ninguém acertou.\n\nEscreva um método.'}>
        <button type="button">3</button>
      </Tooltip>,
    )
    fireEvent.mouseEnter(screen.getByRole('button'))
    const tooltip = screen.getByRole('tooltip')
    expect(tooltip.firstElementChild).toHaveClass('tooltip__title')
    expect(tooltip.firstElementChild).toHaveTextContent('Problema 3 sem conceito')
    expect(tooltip).toHaveTextContent('Ninguém acertou.\n\nEscreva um método.', {
      normalizeWhitespace: false,
    })
  })

  it('has no title element when no title is given', () => {
    render(
      <Tooltip text="Conceitos">
        <button type="button">c</button>
      </Tooltip>,
    )
    fireEvent.mouseEnter(screen.getByRole('button'))
    expect(screen.getByRole('tooltip').children).toHaveLength(0)
  })
})
