// GET /dashboard/mastery/{id} (DASH-01/02/03/05). Gated on a selected assignment: `enabled` keeps the
// query idle until the rail picks an id, so no request fires for a null selection. The response always
// carries the uncertainty frame (first_auc/trained_at), even untrained (dashboard.py D-08).

import { useQuery } from '@tanstack/react-query'

import { fetchJson } from '../api/client'
import type { MasteryResponse } from '../api/schema'

export function useMastery(assignmentId: number | null) {
  return useQuery({
    queryKey: ['mastery', assignmentId],
    queryFn: () => fetchJson<MasteryResponse>(`/dashboard/mastery/${assignmentId}`),
    enabled: assignmentId != null,
    // Optional: poll while untrained (first_auc==null) so a freshly-finished training run surfaces
    // without a manual reload — left off by default to avoid hammering the api (RESEARCH Pattern 2).
    // refetchInterval: (q) => (q.state.data?.first_auc == null ? 5000 : false),
  })
}
