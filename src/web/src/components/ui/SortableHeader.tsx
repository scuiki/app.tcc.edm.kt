import type { ReactNode } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'

import { ColumnLabel } from './DataTable'
import './SortableHeader.css'

interface SortableHeaderProps {
  label: string
  // Null quando a coluna não é a ordenada
  direction: 'asc' | 'desc' | null
  onSort: () => void
  // O marcador antes do botão, para o botão se chamar só pelo rótulo
  leading?: ReactNode
  // A dica com a explicação, ao lado do botão e nunca dentro dele, porque botão não aninha botão
  hint?: ReactNode
}

// O cabeçalho ordenável é um botão dentro do th, e o th diz ao leitor de tela a direção
export function SortableHeader({ label, direction, onSort, leading, hint }: SortableHeaderProps) {
  const ariaSort = direction === 'asc' ? 'ascending' : direction === 'desc' ? 'descending' : 'none'
  const Chevron = direction === 'desc' ? ChevronDown : ChevronUp
  return (
    <th scope="col" aria-sort={ariaSort} className="sortable-header">
      <span className="data-table__th">
        {leading}
        <button type="button" className="sortable-header__button" onClick={onSort}>
          <ColumnLabel text={label} />
          {direction ? <Chevron size={14} aria-hidden="true" /> : null}
        </button>
        {hint}
      </span>
    </th>
  )
}
