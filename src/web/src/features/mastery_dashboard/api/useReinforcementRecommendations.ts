import { useQuery } from '@tanstack/react-query'

import { getJson } from '../../../http/client'
import type { Schema } from '../../../http/types'

export type ReinforcementRecommendation = Schema<'ReinforcementRecommendationDTO'>
type RecommendationsResponse = Schema<'RecommendationsResponseDTO'>

export function useReinforcementRecommendations(assignmentId: number) {
  return useQuery({
    queryKey: ['reinforcement-recommendations', assignmentId],
    queryFn: () =>
      getJson<RecommendationsResponse>(`/mastery-dashboard/${assignmentId}/recommendations`),
  })
}
