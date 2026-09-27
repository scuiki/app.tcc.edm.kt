import { useState } from 'react'

import { InfoHint } from '../../../components/ui/InfoHint'
import { RatioBar } from '../../../components/ui/RatioBar'
import { SortableHeader } from '../../../components/ui/SortableHeader'
import { formatPercent } from '../../../lib/format'
import type { StudentSummary } from '../api/masteryDashboard'
import { MASTERY_HINT } from '../dashboard'
import { sortRows, toggleSort, type SortState } from '../sorting'
import { EstimatedMark } from './EstimatedMark'
import './AnalysisTable.css'

type SortKey = 'student_id' | 'mean_mastery' | 'completed' | 'attempted'

interface StudentsTableProps {
  students: StudentSummary[]
  problemCount: number
  onOpen: (studentId: string) => void
}

// Uma linha por aluno; a ordenação é do professor, e a linha abre o diálogo dele
export function StudentsTable({ students, problemCount, onOpen }: StudentsTableProps) {
  const [sort, setSort] = useState<SortState<SortKey>>({ key: 'mean_mastery', direction: 'asc' })
  const rows = sortRows(students, sort)
  const header = (
    key: SortKey,
    label: React.ReactNode,
    align: 'start' | 'center' | 'end',
    hint?: React.ReactNode,
  ) => (
    <SortableHeader
      align={align}
      direction={sort.key === key ? sort.direction : null}
      onSort={() => setSort(toggleSort(sort, key))}
      hint={hint}
    >
      {label}
    </SortableHeader>
  )
  return (
    <div className="analysis-table__scroll">
      <table className="analysis-table analysis-table--ruled" aria-label="Alunos">
        <thead>
          <tr>
            {header('student_id', 'Aluno', 'start')}
            {header(
              'mean_mastery',
              <>
                <EstimatedMark />
                Domínio
              </>,
              'start',
              <InfoHint text={MASTERY_HINT} />,
            )}
            {header('completed', 'Completou', 'center')}
            {header('attempted', 'Tentou', 'center')}
            <th scope="col">
              <EstimatedMark />
              Conceitos mais fracos
            </th>
          </tr>
        </thead>
        <tbody>
          {rows.map((student) => (
            <tr
              key={student.student_id}
              className="analysis-table__row-button"
              tabIndex={0}
              onClick={() => onOpen(student.student_id)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  onOpen(student.student_id)
                }
              }}
            >
              <td className="analysis-table__name">{student.student_id}</td>
              <td className="analysis-table__bar">
                <RatioBar
                  value={student.mean_mastery}
                  tone="predicted"
                  label={`Domínio estimado do aluno ${student.student_id}`}
                />
              </td>
              <td className="analysis-table__num">
                {student.completed} <span className="analysis-table__sub">de {problemCount}</span>
              </td>
              <td className="analysis-table__num">
                {student.attempted} <span className="analysis-table__sub">de {problemCount}</span>
              </td>
              <td>
                {student.weakest_kcs
                  .map((kc) => `${kc.kc_name} (${formatPercent(kc.mastery)})`)
                  .join(' · ')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
