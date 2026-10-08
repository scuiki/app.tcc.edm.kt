import { useState, type ReactNode } from 'react'
import { Blocks, ChevronRight } from 'lucide-react'

import { ColumnHeader, DataTable } from '../../../components/ui/DataTable'
import { Histogram } from '../../../components/ui/Histogram'
import { InfoHint } from '../../../components/ui/InfoHint'
import { RatioBar } from '../../../components/ui/RatioBar'
import { SortableHeader } from '../../../components/ui/SortableHeader'
import { Tooltip } from '../../../components/ui/Tooltip'
import { formatCount, formatNumber } from '../../../lib/format'
import {
  ANALYSIS_MIN_WIDTH,
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

  const header = (key: SortKey, label: string, leading?: ReactNode, hint?: string) => (
    <SortableHeader
      label={label}
      direction={sort.key === key ? sort.direction : null}
      onSort={() => setSort(toggleSort(sort, key))}
      leading={leading}
      hint={hint ? <InfoHint text={hint} /> : undefined}
    />
  )

  return (
    <DataTable label="Problemas" minWidth={ANALYSIS_MIN_WIDTH}>
      <thead>
        <tr>
          {header('problem_id', 'Problema')}
          {header('success_rate', 'Taxa de acerto')}
          {header(
            'median_attempts_to_complete',
            'Tentativas até completar',
            undefined,
            MEDIAN_ATTEMPTS_HINT,
          )}
          {header('students_completed', 'Alunos que completaram')}
          {header('compile_errors_per_run', 'Erros de compilação por execução')}
          {withModel ? header('mean_mastery', 'Domínio', <EstimatedMark />, MASTERY_HINT) : null}
          {withModel ? (
            <ColumnHeader
              label="Distribuição"
              leading={<EstimatedMark />}
              hint={<InfoHint text={DISTRIBUTION_HINT} />}
            />
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
              <td className="data-table__num">
                {problem.median_attempts_to_complete == null ? (
                  <span className="data-table__missing">—</span>
                ) : (
                  formatNumber(problem.median_attempts_to_complete, 1)
                )}
              </td>
              <td className="data-table__num">
                {formatCount(problem.students_completed)}{' '}
                <span className="data-table__sub">
                  de {formatCount(problem.students_attempted)}
                </span>
              </td>
              <td className="data-table__num">{formatNumber(problem.compile_errors_per_run)}</td>
              {withModel ? (
                <td className="analysis-table__bar">
                  {problem.mean_mastery == null ? (
                    <span className="data-table__missing">—</span>
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
                    <span className="data-table__missing">—</span>
                  )}
                </td>
              ) : null}
            </tr>,
            isOpen ? (
              <tr key={`${problem.problem_id}-concepts`} className="analysis-table__detail">
                <td colSpan={columns}>
                  {problem.kcs.length === 0 ? (
                    <span className="data-table__sub">Sem conceitos aprovados</span>
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
    </DataTable>
  )
}
