// GET /assignments (Pattern 2). The assignment picker's data source — no id needed; it is the entry
// point that produces the ids the other three hooks gate on. fetchJson proxies same-origin to the api
// service (D-01/D-04).

import { useQuery } from '@tanstack/react-query'

import { fetchJson } from '../http/client'
import type { AssignmentsResponse } from '../http/schema'

export function useAssignments() {
  return useQuery({
    queryKey: ['assignments'],
    queryFn: () => fetchJson<AssignmentsResponse>('/assignments'),
  })
}
