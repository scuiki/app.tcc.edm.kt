import type { ReactNode } from 'react'

import './PageHeader.css'

interface PageHeaderProps {
  title: string
  // A etiqueta de situação, ao lado do título e fora dele
  badge?: ReactNode
  description?: string
  // A linha de fatos, abaixo da linha do título
  facts?: ReactNode
  // A ação principal da página, como o botão de criar
  action?: ReactNode
}

// Toda página abre assim, com um único título de página
export function PageHeader({ title, badge, description, facts, action }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-header__text">
        <div className="page-header__row">
          <h1 className="t-page-title">{title}</h1>
          {badge}
        </div>
        {facts}
        {description ? <p className="page-header__description">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}
