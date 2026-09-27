import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'

import './PageHeader.css'

interface PageHeaderProps {
  title: string
  // O ícone da tela, antes do título, quando o título é o nome do registro
  icon?: LucideIcon
  description?: string
  // A ação principal da página, como o botão de criar
  action?: ReactNode
}

// Toda página abre assim, com um único título de página
export function PageHeader({ title, icon: Icon, description, action }: PageHeaderProps) {
  return (
    <div className="page-header">
      <div className="page-header__text">
        <h1 className="t-page-title page-header__title">
          {Icon ? <Icon className="page-header__icon" size={22} aria-hidden="true" /> : null}
          {title}
        </h1>
        {description ? <p className="page-header__description">{description}</p> : null}
      </div>
      {action}
    </div>
  )
}
