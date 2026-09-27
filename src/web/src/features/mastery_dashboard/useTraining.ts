import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { assignmentKeys } from '../assignments/api/useAssignments'
import {
  isTrainingFinished,
  trainingKeys,
  useLossHistory,
  useStartTraining,
  useTrainingJob,
} from '../model_training/api/training'
import { masteryDashboardKeys } from './api/masteryDashboard'

// Ao terminar, o exercício vira treinado, a Análise ganha as colunas e a curva, as últimas épocas
function useRefreshAnalysis(assignmentId: number, jobId: number | null) {
  const queryClient = useQueryClient()
  return () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: trainingKeys.lossHistory(jobId ?? 0) }),
      queryClient.invalidateQueries({ queryKey: assignmentKeys.all }),
      queryClient.invalidateQueries({ queryKey: masteryDashboardKeys.statistics(assignmentId) }),
      queryClient.invalidateQueries({ queryKey: masteryDashboardKeys.mastery(assignmentId) }),
      queryClient.invalidateQueries({ queryKey: masteryDashboardKeys.students(assignmentId) }),
    ])
}

// O treino de um exercício, do clique em Treinar até o job terminar, com o diálogo aberto
export function useTraining(assignmentId: number) {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const start = useStartTraining(assignmentId)
  const jobId = start.data?.job_id ?? null
  const refresh = useRefreshAnalysis(assignmentId, jobId)
  const job = useTrainingJob(jobId, refresh)

  // Enquanto o pedido de início ou o job rodam, o diálogo não fecha e a aba avisa ao sair
  const isRunning = start.isPending || (start.isSuccess && !isTrainingFinished(job.data))
  const lossHistory = useLossHistory(jobId, isRunning)

  function begin() {
    setIsDialogOpen(true)
    start.mutate()
  }

  function close() {
    if (!isRunning) setIsDialogOpen(false)
  }

  return {
    isDialogOpen,
    isRunning,
    start,
    job: job.data,
    epochs: lossHistory.data?.epochs ?? [],
    begin,
    close,
  }
}

export type Training = ReturnType<typeof useTraining>
