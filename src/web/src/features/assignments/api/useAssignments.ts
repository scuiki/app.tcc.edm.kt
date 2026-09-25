import { useQuery } from '@tanstack/react-query'

import { getJson } from '../../../http/client'
import type { Schema } from '../../../http/types'

export type AssignmentSummary = Schema<'AssignmentSummaryDTO'>
type AssignmentsResponse = Schema<'ListAssignmentsResponseDTO'>

export const assignmentKeys = { all: ['assignments'] as const }

export type AssignmentStatus = Schema<'AssignmentStatus'>

// Sem turma, todos os assignments ativos, e com ela só os daquela turma
export function useAssignments(classroomId?: number | null) {
  const path = classroomId == null ? '/assignments' : `/assignments?classroom_id=${classroomId}`
  return useQuery({
    queryKey: [...assignmentKeys.all, classroomId ?? 'all'],
    queryFn: () => getJson<AssignmentsResponse>(path),
  })
}
