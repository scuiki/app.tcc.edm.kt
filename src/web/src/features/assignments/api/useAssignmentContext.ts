import { useClassrooms } from '../../classrooms/api/classrooms'
import { useAssignments } from './useAssignments'

export { ASSIGNMENT_STATUS_LABEL, type AssignmentSummary } from './useAssignments'

// A turma e o exercício que o endereço nomeia, resolvidos pelas listas que o app já carrega
export function useAssignmentContext(classroomId?: number, assignmentId?: number) {
  const classrooms = useClassrooms()
  const assignments = useAssignments(classroomId ?? null)
  const classroom =
    classroomId == null
      ? undefined
      : classrooms.data?.classrooms.find((candidate) => candidate.id === classroomId)
  const list = assignments.data?.assignments ?? []
  const assignment =
    assignmentId == null ? undefined : list.find((candidate) => candidate.id === assignmentId)
  const isPending = classrooms.isPending || (classroomId != null && assignments.isPending)
  const isError = classrooms.isError || assignments.isError
  // Um id que não existe (turma excluída, link velho) dá "não encontrado", não uma tela quebrada
  const isMissing =
    !isPending && !isError && (classroom == null || (assignmentId != null && assignment == null))
  return { classroom, assignment, assignments: list, isPending, isError, isMissing }
}
