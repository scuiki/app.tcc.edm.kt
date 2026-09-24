import type { ReactNode } from 'react'

import './Card.css'

interface CardProps {
  title: string
  // O que fica à direita do título, como uma busca
  actions?: ReactNode
  footer?: ReactNode
  children: ReactNode
}

// O cartão pousa na página pela sombra, sempre com um cabeçalho de 48px
export function Card({ title, actions, footer, children }: CardProps) {
  return (
    <section className="card">
      <header className="card__header">
        <h2 className="card__title">{title}</h2>
        {actions}
      </header>
      <div className="card__body">{children}</div>
      {footer ? <footer className="card__footer">{footer}</footer> : null}
    </section>
  )
}
