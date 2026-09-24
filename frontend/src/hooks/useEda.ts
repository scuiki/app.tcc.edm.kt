// GET /mastery-dashboard/{id}/pre-training-statistics (DASH-04). EDA is training-independent — it reads only the canonical Parquet,
// so it is available the moment an assignment is selected, with or without a trained model. Gated on the
// selected id like the other dashboard hooks.

import { useQuery } from '@tanstack/react-query'

import { fetchJson } from '../api/client'
import type { EdaResponse } from '../api/schema'

export function useEda(assignmentId: number | null) {
  return useQuery({
    queryKey: ['eda', assignmentId],
    queryFn: () => fetchJson<EdaResponse>(`/mastery-dashboard/${assignmentId}/pre-training-statistics`),
    enabled: assignmentId != null,
  })
}
