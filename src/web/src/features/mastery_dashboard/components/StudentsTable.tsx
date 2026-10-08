import { useState, type ReactNode } from 'react'

import { GeneratedByML } from '../../../components/GeneratedByML'
import { ColumnHeader, DataTable } from '../../../components/ui/DataTable'
import { InfoHint } from '../../../components/ui/InfoHint'
import { RatioBar } from '../../../components/ui/RatioBar'
import { SortableHeader } from '../../../components/ui/SortableHeader'
import { formatPercent } from '../../../lib/format'
import type { StudentSummary } from '../api/masteryDashboard'
import { ANALYSIS_MIN_WIDTH, MASTERY_HINT } from '../dashboard'
import { sortRows, toggleSort, type SortState } from '../sorting'
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
  const header = (key: SortKey, label: string, leading?: ReactNode, hint?: ReactNode) => (
    <SortableHeader
      label={label}
      direction={sort.key === key ? sort.direction : null}
      onSort={() => setSort(toggleSort(sort, key))}
      leading={leading}
      hint={hint}
    />
  )
  return (
    <DataTable label="Alunos" minWidth={ANALYSIS_MIN_WIDTH}>
      <thead>
        <tr>
          {header('student_id', 'Aluno')}
          {header('mean_mastery', 'Domínio', <GeneratedByML />, <InfoHint text={MASTERY_HINT} />)}
          {header('completed', 'Completou')}
          {header('attempted', 'Tentou')}
          <ColumnHeader label="Conceitos mais fracos" leading={<GeneratedByML />} />
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
            <td className="data-table__name">{student.student_id}</td>
            <td>
              <RatioBar
                value={student.mean_mastery}
                tone="predicted"
                label={`Domínio estimado do aluno ${student.student_id}`}
              />
            </td>
            <td className="data-table__num">
              {student.completed} <span className="data-table__sub">de {problemCount}</span>
            </td>
            <td className="data-table__num">
              {student.attempted} <span className="data-table__sub">de {problemCount}</span>
            </td>
            <td>
              {student.weakest_kcs
                .map((kc) => `${kc.kc_name} (${formatPercent(kc.mastery)})`)
                .join(' · ')}
            </td>
          </tr>
        ))}
      </tbody>
    </DataTable>
  )
}
