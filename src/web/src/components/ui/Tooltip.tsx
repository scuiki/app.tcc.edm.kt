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

type TooltipSize = 'default' | 'wide'

interface TooltipProps {
  // O texto mantém as quebras de linha, e uma linha em branco separa dois parágrafos
  text: string
  // O título opcional, em negrito numa linha própria acima do texto
  title?: string
  // O largo, de 360px no lugar de 260px, leva o enunciado do problema
  size?: TooltipSize
  // Um elemento só, que recebe os eventos de hover e foco; a dica nasce ao lado, sem invólucro
  children: ReactElement<HTMLAttributes<HTMLElement>>
}

interface Placement {
  top: number
  left: number
  // O diálogo aberto em volta do elemento, ou o body fora de diálogo
  host: Element
}

// Metade da largura máxima de cada tamanho, para o balão centrado nunca sair da janela
const HALF_WIDTH: Record<TooltipSize, number> = { default: 130, wide: 180 }

// A dica aparece na hora do hover ou do foco, porque o title nativo espera quase um segundo
export function Tooltip({ text, title, size = 'default', children }: TooltipProps) {
  const [placement, setPlacement] = useState<Placement | null>(null)

  function show(event: MouseEvent<HTMLElement> | FocusEvent<HTMLElement>) {
    const target = event.currentTarget
    // No foco só com o anel visível, e não quando o diálogo foca o primeiro controle ao abrir
    if (event.type === 'focus' && !target.matches(':focus-visible')) return
    const rect = target.getBoundingClientRect()
    const center = rect.left + rect.width / 2
    const halfWidth = HALF_WIDTH[size]
    setPlacement({
      top: rect.bottom + 6,
      left: Math.min(Math.max(center, halfWidth), window.innerWidth - halfWidth),
      // O dialog modal fica acima de tudo o que está no body, então o balão nasce dentro dele
      host: target.closest('dialog[open]') ?? document.body,
    })
  }

  function hide() {
    setPlacement(null)
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
      {placement
        ? createPortal(
            <span
              role="tooltip"
              className={size === 'wide' ? 'tooltip tooltip--wide' : 'tooltip'}
              style={{ top: placement.top, left: placement.left }}
            >
              {title ? <span className="tooltip__title">{title}</span> : null}
              {text}
            </span>,
            placement.host,
          )
        : null}
    </>
  )
}
