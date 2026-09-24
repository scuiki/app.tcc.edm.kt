import { useQuery } from '@tanstack/react-query'

import { getJson } from '../../../http/client'
import type { Schema } from '../../../http/types'

export type AssignmentSummary = Schema<'AssignmentSummaryDTO'>
type AssignmentsResponse = Schema<'ListAssignmentsResponseDTO'>

export const assignmentKeys = { all: ['assignments'] as const }

export function useAssignments() {
  return useQuery({
    queryKey: assignmentKeys.all,
    queryFn: () => getJson<AssignmentsResponse>('/assignments'),
  })
}
