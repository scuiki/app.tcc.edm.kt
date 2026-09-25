import type { UseQueryResult } from '@tanstack/react-query'

import { EmptyState, QueryStates } from '../../../components/states/states'
import { Card } from '../../../components/ui/Card'
import { SelectField } from '../../../components/ui/SelectField'
import type { AssignmentSummary } from '../../assignments/api/useAssignments'
import type { ClassroomSummary } from '../../classrooms/api/classrooms'
import { AssignmentStatusBadge } from './AssignmentStatusBadge'
import './AssignmentPicker.css'

interface AssignmentPickerProps {
  classrooms: ClassroomSummary[]
  classroomId: number | null
  onClassroomChange: (classroomId: number) => void
  assignmentsQuery: UseQueryResult<{ assignments: AssignmentSummary[] }>
  assignmentId: number | null
  onAssignmentChange: (assignmentId: number) => void
}

export function AssignmentPicker({
  classrooms,
  classroomId,
  onClassroomChange,
  assignmentsQuery,
  assignmentId,
  onAssignmentChange,
}: AssignmentPickerProps) {
  return (
    <Card title="Exercícios">
      <div className="assignment-picker__classroom">
        <SelectField
          label="Turma"
          placeholder="Escolha a turma"
          value={classroomId == null ? '' : String(classroomId)}
          options={classrooms.map(({ id, name }) => ({ value: String(id), label: name }))}
          onChange={(value) => onClassroomChange(Number(value))}
        />
      </div>
      {classroomId == null ? null : (
        <QueryStates
          query={assignmentsQuery}
          loadingLabel="Carregando exercícios…"
          isEmpty={(data) => data.assignments.length === 0}
          empty={
            <EmptyState
              text="Esta turma ainda não tem exercícios. Importe os dados dela primeiro."
              action={<a href="#/classroom-imports">Importar dados</a>}
            />
          }
        >
          {(data) => (
            <ul className="assignment-picker__list">
              {data.assignments.map((assignment) => (
                <li key={assignment.id}>
                  <button
                    type="button"
                    className="assignment-picker__item"
                    aria-current={assignment.id === assignmentId ? 'true' : undefined}
                    onClick={() => onAssignmentChange(assignment.id)}
                  >
                    <span className="assignment-picker__name">{assignment.name}</span>
                    <AssignmentStatusBadge status={assignment.status} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </QueryStates>
      )}
    </Card>
  )
}
