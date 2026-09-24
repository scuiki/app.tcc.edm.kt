import type { ReactNode } from 'react'

import './PageHeader.css'

interface PageHeaderProps {
  title: string
  description?: string
  // A ação principal da página, como o botão de criar
  action?: ReactNode
}

// Toda página abre assim, com um único título de página
export function PageHeader({ title, description, action }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-header__text">
        <h1 className="t-page-title">{title}</h1>
        {description ? <p className="page-header__description">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}
