import { useQuery } from '@tanstack/react-query'

import { getJson } from '../../../http/client'
import type { Schema } from '../../../http/types'

export type SubmissionStatistics = Schema<'SubmissionStatisticsResponseDTO'>
export type ProblemStatistics = Schema<'ProblemStatisticsDTO'>
export type KnowledgeComponentStatistics = Schema<'KnowledgeComponentStatisticsDTO'>
export type Mastery = Schema<'MasteryResponseDTO'>
export type TrainedModel = Schema<'TrainedModelDTO'>
export type KnowledgeComponentMastery = Schema<'KnowledgeComponentMasteryDTO'>
export type ProblemMastery = Schema<'ProblemMasteryDTO'>
export type StudentSummary = Schema<'StudentSummaryDTO'>
export type StudentDetail = Schema<'StudentDetailDTO'>
type StudentsResponse = Schema<'ListStudentsResponseDTO'>

export const masteryDashboardKeys = {
  statistics: (assignmentId: number) => ['submission-statistics', assignmentId] as const,
  mastery: (assignmentId: number) => ['mastery', assignmentId] as const,
  students: (assignmentId: number) => ['students', assignmentId] as const,
  student: (assignmentId: number, studentId: string) =>
    ['student', assignmentId, studentId] as const,
}

// O que aconteceu nas execuções, contado sem modelo e disponível desde a importação
export function useSubmissionStatistics(assignmentId: number) {
  return useQuery({
    queryKey: masteryDashboardKeys.statistics(assignmentId),
    queryFn: () =>
      getJson<SubmissionStatistics>(`/mastery-dashboard/${assignmentId}/submission-statistics`),
  })
}

// O que o modelo prevê por conceito e por problema, com a distribuição dos alunos
export function useMastery(assignmentId: number) {
  return useQuery({
    queryKey: masteryDashboardKeys.mastery(assignmentId),
    queryFn: () => getJson<Mastery>(`/mastery-dashboard/${assignmentId}/mastery`),
  })
}

// A lista inteira, leve, e a ordenação fica no front
export function useStudents(assignmentId: number) {
  return useQuery({
    queryKey: masteryDashboardKeys.students(assignmentId),
    queryFn: () => getJson<StudentsResponse>(`/mastery-dashboard/${assignmentId}/students`),
  })
}

// O detalhe é outra rota, buscada só quando o diálogo do aluno abre
export function useStudent(assignmentId: number, studentId: string) {
  return useQuery({
    queryKey: masteryDashboardKeys.student(assignmentId, studentId),
    queryFn: () =>
      getJson<StudentDetail>(`/mastery-dashboard/${assignmentId}/students/${studentId}`),
  })
}
