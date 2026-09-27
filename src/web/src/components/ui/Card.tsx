import type { ReactNode } from 'react'

import './Card.css'

interface CardProps {
  // Sem título o cartão começa direto no conteúdo, como o da Análise, que abre nas abas
  title?: string
  // O que fica à direita do título, como uma busca
  actions?: ReactNode
  footer?: ReactNode
  children: ReactNode
}

// O cartão pousa na página pela sombra, sempre com um cabeçalho de 48px
export function Card({ title, actions, footer, children }: CardProps) {
  return (
    <section className="card">
      {title ? (
        <header className="card__header">
          <h2 className="card__title">{title}</h2>
          {actions}
        </header>
      ) : null}
      <div className="card__body">{children}</div>
      {footer ? <footer className="card__footer">{footer}</footer> : null}
    </section>
  )
}
