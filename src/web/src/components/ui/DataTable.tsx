import type { ReactNode } from 'react'

import { Tooltip } from './Tooltip'
import './DataTable.css'

interface DataTableProps {
  // O nome da tabela para o leitor de tela
  label?: string
  // A largura mínima fica com quem precisa dela, e abaixo dela a tabela rola de lado
  minWidth?: number
  children: ReactNode
}

// A tabela comum do app, com o nome à esquerda, os números ao centro e os botões à direita
export function DataTable({ label, minWidth, children }: DataTableProps) {
  return (
    <div className="data-table__scroll">
      <table className="data-table" aria-label={label} style={minWidth ? { minWidth } : undefined}>
        {children}
      </table>
    </div>
  )
}

// O rótulo longo trunca com reticências, e o balão mostra o texto inteiro no hover
export function ColumnLabel({ text }: { text: string }) {
  return (
    <Tooltip text={text}>
      <span className="data-table__label">{text}</span>
    </Tooltip>
  )
}

interface ColumnHeaderProps {
  label: string
  // O marcador antes do rótulo, como o cérebro das colunas que vêm do modelo
  leading?: ReactNode
  // A dica com a explicação, depois do rótulo
  hint?: ReactNode
}

// O cabeçalho de uma coluna que não ordena, com a mesma estrutura do ordenável
export function ColumnHeader({ label, leading, hint }: ColumnHeaderProps) {
  return (
    <th scope="col">
      <span className="data-table__th">
        {leading}
        <ColumnLabel text={label} />
        {hint}
      </span>
    </th>
  )
}
