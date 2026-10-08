import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getJson, sendJson } from '../../../http/client'
import type { Schema } from '../../../http/types'
import { assignmentKeys } from '../../assignments/api/useAssignments'

export type ProblemKnowledgeComponents = Schema<'ProblemKnowledgeComponentsDTO'>
export type AssignmentProblems = Schema<'ListProblemKnowledgeComponentsResponseDTO'>
export type KnowledgeComponent = Schema<'KnowledgeComponentDTO'>
export type GenerationJob = Schema<'KnowledgeComponentGenerationJobDTO'>
type StartedJob = Schema<'StartedJobDTO'>

export const knowledgeComponentKeys = {
  problemsOf: (assignmentId: number) => ['problem-knowledge-components', assignmentId] as const,
  job: (jobId: number) => ['knowledge-component-generation-job', jobId] as const,
}

// Os problemas do exercício, cada um com os conceitos que exige
export function useAssignmentProblems(assignmentId: number) {
  return useQuery({
    queryKey: knowledgeComponentKeys.problemsOf(assignmentId),
    queryFn: () =>
      getJson<AssignmentProblems>(`/assignments/${assignmentId}/problems/knowledge-components`),
  })
}

export function isJobFinished(job: GenerationJob | undefined) {
  return job?.status === 'done' || job?.status === 'failed'
}

// O job roda num subprocess, então a tela consulta a cada 2s até ele terminar
export function useGenerationJob(jobId: number | null, onFinished: () => void) {
  return useQuery({
    queryKey: knowledgeComponentKeys.job(jobId ?? 0),
    queryFn: async () => {
      const job = await getJson<GenerationJob>(`/knowledge-components/generation-jobs/${jobId}`)
      if (isJobFinished(job)) onFinished()
      return job
    },
    enabled: jobId != null,
    refetchInterval: (query) => (isJobFinished(query.state.data) ? false : 2000),
  })
}

// Toda edição muda os conceitos do exercício e pode mudar a situação dele
export function useRefreshAssignment(assignmentId: number) {
  const queryClient = useQueryClient()
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: knowledgeComponentKeys.problemsOf(assignmentId) }),
      queryClient.invalidateQueries({ queryKey: assignmentKeys.all }),
    ])
}

export function useStartGeneration(assignmentId: number) {
  return useMutation({
    mutationFn: () =>
      sendJson<StartedJob>('POST', '/knowledge-components/generation-jobs', {
        assignment_id: assignmentId,
      }),
  })
}

export function useCreateKnowledgeComponent(assignmentId: number) {
  const invalidate = useRefreshAssignment(assignmentId)
  return useMutation({
    mutationFn: ({ name, problemIds }: { name: string; problemIds: number[] }) =>
      sendJson<KnowledgeComponent>('POST', '/knowledge-components', {
        assignment_id: assignmentId,
        name,
        problem_ids: problemIds,
      }),
    onSuccess: invalidate,
  })
}

export function useLinkKnowledgeComponent(assignmentId: number) {
  const invalidate = useRefreshAssignment(assignmentId)
  return useMutation({
    mutationFn: ({ kcId, problemId }: { kcId: number; problemId: number }) =>
      sendJson<unknown>('POST', `/knowledge-components/${kcId}/problems/${problemId}`),
    onSuccess: invalidate,
  })
}

export function useUnlinkKnowledgeComponent(assignmentId: number) {
  const invalidate = useRefreshAssignment(assignmentId)
  return useMutation({
    mutationFn: ({ kcId, problemId }: { kcId: number; problemId: number }) =>
      sendJson<unknown>('DELETE', `/knowledge-components/${kcId}/problems/${problemId}`),
    onSuccess: invalidate,
  })
}

export function useRenameKnowledgeComponent(assignmentId: number) {
  const invalidate = useRefreshAssignment(assignmentId)
  return useMutation({
    mutationFn: ({ kcId, name }: { kcId: number; name: string }) =>
      sendJson<KnowledgeComponent>('PUT', `/knowledge-components/${kcId}`, { name }),
    onSuccess: invalidate,
  })
}

export function useRemoveKnowledgeComponent(assignmentId: number) {
  const invalidate = useRefreshAssignment(assignmentId)
  return useMutation({
    mutationFn: (kcId: number) => sendJson<unknown>('DELETE', `/knowledge-components/${kcId}`),
    onSuccess: invalidate,
  })
}

export function useApproveKnowledgeComponents(assignmentId: number) {
  const invalidate = useRefreshAssignment(assignmentId)
  return useMutation({
    mutationFn: () =>
      sendJson<unknown>('POST', '/knowledge-components/approve', { assignment_id: assignmentId }),
    onSuccess: invalidate,
  })
}
