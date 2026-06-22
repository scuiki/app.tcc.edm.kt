// GET /dashboard/recommendations/{id} (REC-01). Pre-rendered pt-BR `text` per suggestion, weakest-first;
// the SPA shows it verbatim (RecommendationList). Gated on the selected id; an untrained assignment
// returns an empty recommendations array (no model → no ranking yet).

import { useQuery } from '@tanstack/react-query'

import { fetchJson } from '../api/client'
import type { RecommendationsResponse } from '../api/schema'

export function useRecommendations(assignmentId: number | null) {
  return useQuery({
    queryKey: ['recs', assignmentId],
    queryFn: () => fetchJson<RecommendationsResponse>(`/dashboard/recommendations/${assignmentId}`),
    enabled: assignmentId != null,
  })
}
