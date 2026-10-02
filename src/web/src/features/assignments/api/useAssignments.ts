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

// O nome humano de cada situação, que as telas de Conceitos e de Análise mostram na etiqueta
export const ASSIGNMENT_STATUS_LABEL: Record<AssignmentStatus, string> = {
  statistics_only: 'Só estatísticas',
  ready_for_kc_generation: 'Pronto para conceitos',
  kc_draft: 'Rascunho de conceitos',
  kc_approved: 'Conceitos aprovados',
  trained: 'Modelo treinado',
}
