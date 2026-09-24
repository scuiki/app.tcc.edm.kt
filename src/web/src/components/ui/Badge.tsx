import type { ReactNode } from 'react'

import './Badge.css'

// Sem vermelho, âmbar ou verde, e só o azul suave destaca, como no modelo treinado
type BadgeTone = 'neutral' | 'accent'

export function Badge({ tone, children }: { tone: BadgeTone; children: ReactNode }) {
  return <span className={`badge badge--${tone}`}>{children}</span>
}
