import { useState } from 'react'

import {
  isJobFinished,
  useGenerationJob,
  useRefreshAssignment,
  useStartGeneration,
} from './api/knowledgeComponents'

// A extração de um exercício, do clique em Extrair até o job terminar, com o diálogo aberto
export function useExtraction(assignmentId: number) {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const start = useStartGeneration(assignmentId)
  const refresh = useRefreshAssignment(assignmentId)
  const job = useGenerationJob(start.data?.job_id ?? null, refresh)

  // Enquanto o pedido de início ou o job rodam, o diálogo não fecha e a aba avisa ao sair
  const isRunning = start.isPending || (start.isSuccess && !isJobFinished(job.data))

  function begin() {
    setIsDialogOpen(true)
    start.mutate()
  }

  function close() {
    if (!isRunning) setIsDialogOpen(false)
  }

  return { isDialogOpen, isRunning, start, job: job.data, begin, close }
}

export type Extraction = ReturnType<typeof useExtraction>
