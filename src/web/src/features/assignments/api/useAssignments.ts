import { useQuery } from '@tanstack/react-query'
import { Blocks, Brain, type LucideIcon } from 'lucide-react'

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

// O nome humano de cada situação, que as telas e o menu mostram
export const ASSIGNMENT_STATUS_LABEL: Record<AssignmentStatus, string> = {
  statistics_only: 'Só estatísticas',
  ready_for_kc_generation: 'Pronto para conceitos',
  kc_draft: 'Rascunho de conceitos',
  kc_approved: 'Conceitos aprovados',
  trained: 'Treinado',
}

// O ícone da etapa na etiqueta, os blocos nas de conceitos e o cérebro no treinado
export const ASSIGNMENT_STATUS_ICON: Record<AssignmentStatus, LucideIcon | undefined> = {
  statistics_only: undefined,
  ready_for_kc_generation: Blocks,
  kc_draft: Blocks,
  kc_approved: Blocks,
  trained: Brain,
}

// O tom, o ícone e o rótulo da etiqueta de situação, com o azul só no exercício treinado
export function assignmentStatusBadge(status: AssignmentStatus) {
  return {
    tone: status === 'trained' ? ('model' as const) : ('neutral' as const),
    icon: ASSIGNMENT_STATUS_ICON[status],
    label: ASSIGNMENT_STATUS_LABEL[status],
  }
}
