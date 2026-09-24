import { useQuery } from '@tanstack/react-query'

import { getJson } from '../../../http/client'
import type { Schema } from '../../../http/types'

export type PreTrainingStatistics = Schema<'PreTrainingStatisticsResponseDTO'>
// As chaves inteiras do backend chegam como texto no JSON
export type StatisticSeries = Record<string, number>

export function usePreTrainingStatistics(assignmentId: number) {
  return useQuery({
    queryKey: ['pre-training-statistics', assignmentId],
    queryFn: () =>
      getJson<PreTrainingStatistics>(`/mastery-dashboard/${assignmentId}/pre-training-statistics`),
  })
}
