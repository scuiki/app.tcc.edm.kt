import type { ReactNode } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

import './SortableHeader.css'

interface SortableHeaderProps {
  children: ReactNode
  // Null quando a coluna não é a ordenada
  direction: 'asc' | 'desc' | null
  onSort: () => void
  align?: 'start' | 'center' | 'end'
  // A dica com a explicação, ao lado do botão e nunca dentro dele, porque botão não aninha botão
  hint?: ReactNode
}

// O cabeçalho ordenável é um botão dentro do th, e o th diz ao leitor de tela a direção
export function SortableHeader({
  children,
  direction,
  onSort,
  align = 'start',
  hint,
}: SortableHeaderProps) {
  const ariaSort = direction === 'asc' ? 'ascending' : direction === 'desc' ? 'descending' : 'none'
  const Chevron = direction === 'desc' ? ChevronDown : ChevronUp
  return (
    <th scope="col" aria-sort={ariaSort} className={`sortable-header sortable-header--${align}`}>
      <span className="sortable-header__content">
        <button type="button" className="sortable-header__button" onClick={onSort}>
          <span>{children}</span>
          {direction ? <Chevron size={13} aria-hidden="true" /> : null}
        </button>
        {hint}
      </span>
    </th>
  )
}
