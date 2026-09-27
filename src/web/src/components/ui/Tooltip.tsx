import {
  cloneElement,
  useState,
  type FocusEvent,
  type HTMLAttributes,
  type MouseEvent,
  type ReactElement,
} from 'react'
import { createPortal } from 'react-dom'

import './Tooltip.css'

interface TooltipProps {
  text: string
  // Um elemento só, que recebe os eventos de hover e foco; a dica nasce ao lado, sem invólucro
  children: ReactElement<HTMLAttributes<HTMLElement>>
}

interface Position {
  top: number
  left: number
}

const HALF_WIDTH = 130

// A dica aparece na hora do hover ou do foco, porque o title nativo espera quase um segundo
export function Tooltip({ text, children }: TooltipProps) {
  const [position, setPosition] = useState<Position | null>(null)

  function show(event: MouseEvent<HTMLElement> | FocusEvent<HTMLElement>) {
    const rect = event.currentTarget.getBoundingClientRect()
    const center = rect.left + rect.width / 2
    setPosition({
      top: rect.bottom + 6,
      left: Math.min(Math.max(center, HALF_WIDTH), window.innerWidth - HALF_WIDTH),
    })
  }

  function hide() {
    setPosition(null)
  }

  const anchor = cloneElement(children, {
    onMouseEnter: show,
    onMouseLeave: hide,
    onFocus: show,
    onBlur: hide,
  })
  return (
    <>
      {anchor}
      {position
        ? createPortal(
            <span role="tooltip" className="tooltip" style={position}>
              {text}
            </span>,
            document.body,
          )
        : null}
    </>
  )
}
