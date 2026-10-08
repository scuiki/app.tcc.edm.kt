import type { ReactNode } from 'react'

import './PageHeader.css'

interface PageHeaderProps {
  title: string
  // A etiqueta de situação, ao lado do título e fora dele
  badge?: ReactNode
  description?: string
  // A ação principal da página, como o botão de criar
  action?: ReactNode
}

// Toda página abre assim, com um único título de página
export function PageHeader({ title, badge, description, action }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-header__text">
        <div className="page-header__row">
          <h1 className="t-page-title">{title}</h1>
          {badge}
        </div>
        {description ? <p className="page-header__description">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}
