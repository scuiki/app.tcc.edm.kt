import type { ReactNode } from 'react'
import { CircleAlert } from 'lucide-react'

import './OutcomeMessage.css'

interface OutcomeMessageProps {
  // O vermelho marca a recusa, e o neutro o que não é culpa do pacote, como o sistema ocupado
  tone: 'danger' | 'neutral'
  title: string
  children: ReactNode
}

// Diz o que houve e por quê, e o ! vermelho só aparece na recusa
export function OutcomeMessage({ tone, title, children }: OutcomeMessageProps) {
  return (
    <div className={`outcome outcome--${tone}`} role={tone === 'danger' ? 'alert' : 'status'}>
      {tone === 'danger' ? (
        <CircleAlert className="outcome__icon" size={18} aria-hidden="true" />
      ) : null}
      <div className="outcome__text">
        <span className="outcome__title">{title}</span>
        <span className="outcome__body">{children}</span>
      </div>
    </div>
  )
}
