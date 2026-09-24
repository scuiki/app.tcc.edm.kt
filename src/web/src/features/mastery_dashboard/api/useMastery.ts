import { useQuery } from '@tanstack/react-query'

import { getJson } from '../../../http/client'
import type { Schema } from '../../../http/types'

export type MasteryResponse = Schema<'MasteryResponseDTO'>
export type StudentMastery = Schema<'StudentMasteryDTO'>
export type CriticalKnowledgeComponent = Schema<'CriticalKnowledgeComponentDTO'>

export function useMastery(assignmentId: number) {
  return useQuery({
    queryKey: ['mastery', assignmentId],
    queryFn: () => getJson<MasteryResponse>(`/mastery-dashboard/${assignmentId}/mastery`),
  })
}
