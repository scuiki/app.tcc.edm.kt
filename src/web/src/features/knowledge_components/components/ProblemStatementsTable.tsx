import { CircleAlert } from 'lucide-react'

import { ColumnHeader, DataTable } from '../../../components/ui/DataTable'
import { formatCount } from '../../../lib/format'
import type { ProblemKnowledgeComponents } from '../api/knowledgeComponents'
import './ProblemStatementsTable.css'

// As larguras do colgroup, e o enunciado fica com a sobra do cartão
const PROBLEM_WIDTH = 120
const STATEMENT_MIN_WIDTH = 240
const COUNT_WIDTH = 110

// Cada problema com o enunciado do pacote e quantos conceitos ele tem, só para consulta
export function ProblemStatementsTable({ problems }: { problems: ProblemKnowledgeComponents[] }) {
  return (
    <DataTable
      label="Problemas"
      minWidth={PROBLEM_WIDTH + STATEMENT_MIN_WIDTH + COUNT_WIDTH}
      fixedLayout
    >
      <colgroup>
        <col style={{ width: PROBLEM_WIDTH }} />
        <col />
        <col style={{ width: COUNT_WIDTH }} />
      </colgroup>
      <thead>
        <tr>
          <ColumnHeader label="Problema" />
          <ColumnHeader label="Enunciado" className="data-table__left" />
          <ColumnHeader label="Conceitos" />
        </tr>
      </thead>
      <tbody>
        {problems.map((problem) => (
          <tr key={problem.problem_id}>
            <td className="data-table__name">{problem.problem_id}</td>
            <td className="data-table__wrap data-table__left">
              {problem.statement ?? <span className="data-table__missing">sem enunciado</span>}
            </td>
            <td className="data-table__num">
              {problem.knowledge_components.length === 0 ? (
                <span className="problem-statements__zero">
                  <CircleAlert size={13} aria-hidden="true" />0
                </span>
              ) : (
                formatCount(problem.knowledge_components.length)
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  )
}
