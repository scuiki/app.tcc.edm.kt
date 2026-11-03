import { useMutation, useQuery } from '@tanstack/react-query'

import { getJson, sendJson } from '../../../http/client'
import type { Schema } from '../../../http/types'

export type TrainingJob = Schema<'TrainingJobDTO'>
type StartedTrainingJob = Schema<'StartedTrainingJobDTO'>

export const trainingKeys = {
  job: (jobId: number) => ['training-job', jobId] as const,
}

export function isTrainingFinished(job: TrainingJob | undefined) {
  return job?.status === 'done' || job?.status === 'failed'
}

export function useStartTraining(assignmentId: number) {
  return useMutation({
    mutationFn: () =>
      sendJson<StartedTrainingJob>('POST', '/training-jobs', { assignment_id: assignmentId }),
  })
}

// O treino roda num subprocess, então a tela consulta a cada 2s até ele terminar
export function useTrainingJob(jobId: number | null, onFinished: () => void) {
  return useQuery({
    queryKey: trainingKeys.job(jobId ?? 0),
    queryFn: async () => {
      const job = await getJson<TrainingJob>(`/training-jobs/${jobId}`)
      if (isTrainingFinished(job)) onFinished()
      return job
    },
    enabled: jobId != null,
    refetchInterval: (query) => (isTrainingFinished(query.state.data) ? false : 2000),
  })
}
