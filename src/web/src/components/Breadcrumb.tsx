import type { ReactNode } from 'react'

import './Breadcrumb.css'

export interface Crumb {
  label: string
  // Sem href é o lugar atual
  href?: string
}

interface BreadcrumbProps {
  items: Crumb[]
  // O que fica à direita do caminho, como a etiqueta de situação do exercício
  aside?: ReactNode
}

// O caminho até aqui, com links de volta, repetindo o que o menu marca
export function Breadcrumb({ items, aside }: BreadcrumbProps) {
  return (
    <nav aria-label="Caminho" className="breadcrumb">
      <ol className="breadcrumb__list">
        {items.map((item, index) => (
          <li key={`${item.label}-${index}`} className="breadcrumb__item">
            {index > 0 ? (
              <span className="breadcrumb__separator" aria-hidden="true">
                ›
              </span>
            ) : null}
            {item.href ? (
              <a href={`#${item.href}`}>{item.label}</a>
            ) : (
              <span aria-current="page" className="breadcrumb__current">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
      {aside}
    </nav>
  )
}
