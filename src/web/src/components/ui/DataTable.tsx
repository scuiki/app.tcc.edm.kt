import { useState, type ReactNode } from 'react'

import { Tooltip } from './Tooltip'
import './DataTable.css'

interface DataTableProps {
  // O nome da tabela para o leitor de tela
  label?: string
  // A largura mínima fica com quem precisa dela, e abaixo dela a tabela rola de lado
  minWidth?: number
  // As colunas tomam a largura do colgroup de quem usa, e não a do conteúdo
  fixedLayout?: boolean
  // A primeira coluna fica presa na rolagem lateral, como o nome do conceito na matriz
  stickyFirstColumn?: boolean
  children: ReactNode
}

// A tabela comum do app, com o nome à esquerda, os números ao centro e os botões à direita
export function DataTable({
  label,
  minWidth,
  fixedLayout = false,
  stickyFirstColumn = false,
  children,
}: DataTableProps) {
  // O fio da coluna presa só aparece quando há coluna rolada por baixo dela
  const [isScrolled, setIsScrolled] = useState(false)
  const tableClass = [
    'data-table',
    fixedLayout ? 'data-table--fixed' : null,
    stickyFirstColumn ? 'data-table--sticky' : null,
  ]
    .filter(Boolean)
    .join(' ')
  return (
    <div
      className={isScrolled ? 'data-table__scroll is-scrolled' : 'data-table__scroll'}
      onScroll={
        stickyFirstColumn ? (event) => setIsScrolled(event.currentTarget.scrollLeft > 0) : undefined
      }
    >
      <table className={tableClass} aria-label={label} style={minWidth ? { minWidth } : undefined}>
        {children}
      </table>
    </div>
  )
}

interface ColumnLabelProps {
  text: string
  // Sem o teto de 150px, o rótulo vai até a largura da célula, como o nome do conceito na matriz
  fillCell?: boolean
}

// O rótulo longo trunca com reticências, e o balão mostra o texto inteiro no hover
export function ColumnLabel({ text, fillCell = false }: ColumnLabelProps) {
  return (
    <Tooltip text={text}>
      <span
        className={fillCell ? 'data-table__label data-table__label--fill' : 'data-table__label'}
      >
        {text}
      </span>
    </Tooltip>
  )
}

interface ColumnHeaderProps {
  label: string
  // O marcador antes do rótulo, como o cérebro das colunas que vêm do modelo
  leading?: ReactNode
  // A dica com a explicação, depois do rótulo
  hint?: ReactNode
  // A classe da célula, como a que alinha à esquerda o cabeçalho do texto longo
  className?: string
}

// O cabeçalho de uma coluna que não ordena, com a mesma estrutura do ordenável
export function ColumnHeader({ label, leading, hint, className }: ColumnHeaderProps) {
  return (
    <th scope="col" className={className}>
      <span className="data-table__th">
        {leading}
        <ColumnLabel text={label} />
        {hint}
      </span>
    </th>
  )
}
