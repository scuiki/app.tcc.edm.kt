import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

import './Badge.css'

// Sem vermelho, âmbar ou verde, e só o azul do modelo destaca, na etiqueta Treinado
type BadgeTone = 'neutral' | 'model'

interface BadgeProps {
  tone: BadgeTone
  // O ícone da etapa, que a situação escolhe e a etiqueta só desenha
  icon?: LucideIcon
  children: ReactNode
}

export function Badge({ tone, icon: Icon, children }: BadgeProps) {
  return (
    <span className={`badge badge--${tone}`}>
      {Icon ? (
        <span className="badge__icon">
          <Icon size={13} aria-hidden="true" />
        </span>
      ) : null}
      {children}
    </span>
  )
}
