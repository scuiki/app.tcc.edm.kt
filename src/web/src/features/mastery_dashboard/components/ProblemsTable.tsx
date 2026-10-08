import { useState } from 'react'
import { Blocks, ChevronRight } from 'lucide-react'

import { Histogram } from '../../../components/ui/Histogram'
import { InfoHint } from '../../../components/ui/InfoHint'
import { RatioBar } from '../../../components/ui/RatioBar'
import { SortableHeader } from '../../../components/ui/SortableHeader'
import { Tooltip } from '../../../components/ui/Tooltip'
import { formatCount, formatNumber } from '../../../lib/format'
import {
  DISTRIBUTION_HINT,
  MASTERY_HINT,
  MEDIAN_ATTEMPTS_HINT,
  type ProblemRow,
} from '../dashboard'
import { sortRows, toggleSort, type SortState } from '../sorting'
import { ConceptChips } from './ConceptChips'
import { EstimatedMark } from './EstimatedMark'
import './AnalysisTable.css'

type SortKey =
  | 'problem_id'
  | 'success_rate'
  | 'median_attempts_to_complete'
  | 'students_completed'
  | 'compile_errors_per_run'
  | 'mean_mastery'

interface ProblemsTableProps {
  problems: ProblemRow[]
  // Com modelo, as duas colunas estimadas entram à direita
  withModel: boolean
}

// Uma linha por problema; a seta abre os conceitos que ele exige
export function ProblemsTable({ problems, withModel }: ProblemsTableProps) {
  const [sort, setSort] = useState<SortState<SortKey>>({ key: 'success_rate', direction: 'asc' })
  const [expanded, setExpanded] = useState<number[]>([])
  const rows = sortRows(problems, sort)
  const columns = withModel ? 7 : 5

  function toggleExpanded(problemId: number) {
    setExpanded((current) =>
      current.includes(problemId)
        ? current.filter((id) => id !== problemId)
        : [...current, problemId],
    )
  }

  const header = (
    key: SortKey,
    label: string,
    align: 'start' | 'center' | 'end',
    hint?: string,
  ) => (
    <SortableHeader
      align={align}
      direction={sort.key === key ? sort.direction : null}
      onSort={() => setSort(toggleSort(sort, key))}
      hint={hint ? <InfoHint text={hint} /> : undefined}
    >
      {label}
    </SortableHeader>
  )

  return (
    <div className="analysis-table__scroll">
      <table className="analysis-table" aria-label="Problemas">
        <thead>
          <tr>
            {header('problem_id', 'Problema', 'start')}
            {header('success_rate', 'Taxa de acerto', 'start')}
            {header(
              'median_attempts_to_complete',
              'Tentativas até completar',
              'center',
              MEDIAN_ATTEMPTS_HINT,
            )}
            {header('students_completed', 'Alunos que completaram', 'center')}
            {header('compile_errors_per_run', 'Erros de compilação por execução', 'center')}
            {withModel ? (
              <SortableHeader
                direction={sort.key === 'mean_mastery' ? sort.direction : null}
                onSort={() => setSort(toggleSort(sort, 'mean_mastery'))}
                hint={<InfoHint text={MASTERY_HINT} />}
              >
                <EstimatedMark />
                Domínio
              </SortableHeader>
            ) : null}
            {withModel ? (
              <th scope="col">
                <EstimatedMark />
                Distribuição
                <InfoHint text={DISTRIBUTION_HINT} />
              </th>
            ) : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((problem) => {
            const isOpen = expanded.includes(problem.problem_id)
            return [
              <tr key={problem.problem_id}>
                <td>
                  <button
                    type="button"
                    className="analysis-table__expand"
                    aria-expanded={isOpen}
                    onClick={() => toggleExpanded(problem.problem_id)}
                  >
                    <ChevronRight size={14} aria-hidden="true" />
                    Problema {problem.problem_id}
                  </button>
                </td>
                <td className="analysis-table__bar">
                  <RatioBar
                    value={problem.success_rate}
                    tone="observed"
                    label={`Taxa de acerto do problema ${problem.problem_id}`}
                  />
                </td>
                <td className="analysis-table__num">
                  {problem.median_attempts_to_complete == null ? (
                    <span className="analysis-table__missing">—</span>
                  ) : (
                    formatNumber(problem.median_attempts_to_complete, 1)
                  )}
                </td>
                <td className="analysis-table__num">
                  {formatCount(problem.students_completed)}{' '}
                  <span className="analysis-table__sub">
                    de {formatCount(problem.students_attempted)}
                  </span>
                </td>
                <td className="analysis-table__num">
                  {formatNumber(problem.compile_errors_per_run)}
                </td>
                {withModel ? (
                  <td className="analysis-table__bar">
                    {problem.mean_mastery == null ? (
                      <span className="analysis-table__missing">—</span>
                    ) : (
                      <RatioBar
                        value={problem.mean_mastery}
                        tone="predicted"
                        label={`Domínio estimado no problema ${problem.problem_id}`}
                      />
                    )}
                  </td>
                ) : null}
                {withModel ? (
                  <td className="analysis-table__hist">
                    {problem.histogram ? (
                      <Histogram
                        bins={problem.histogram}
                        unit="alunos"
                        axis={false}
                        label={`Distribuição dos alunos no problema ${problem.problem_id}`}
                      />
                    ) : (
                      <span className="analysis-table__missing">—</span>
                    )}
                  </td>
                ) : null}
              </tr>,
              isOpen ? (
                <tr key={`${problem.problem_id}-concepts`} className="analysis-table__detail">
                  <td colSpan={columns}>
                    {problem.kcs.length === 0 ? (
                      <span className="analysis-table__sub">Sem conceitos aprovados</span>
                    ) : (
                      <ConceptChips
                        concepts={problem.kcs}
                        leading={
                          <Tooltip text="Conceitos">
                            <span
                              className="analysis-table__concepts-icon"
                              role="img"
                              aria-label="Conceitos"
                            >
                              <Blocks size={14} aria-hidden="true" />
                            </span>
                          </Tooltip>
                        }
                      />
                    )}
                  </td>
                </tr>
              ) : null,
            ]
          })}
        </tbody>
      </table>
    </div>
  )
}
