import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { getJson, sendJson } from '../../../http/client'
import type { Schema } from '../../../http/types'
import { assignmentKeys } from '../../assignments/api/useAssignments'

export type ClassroomSummary = Schema<'ClassroomSummaryDTO'>
export type ClassroomStatus = Schema<'ClassroomStatus'>
type ClassroomsResponse = Schema<'ListClassroomsResponseDTO'>
type Classroom = Schema<'ClassroomDTO'>

export const classroomKeys = { all: ['classrooms'] as const }

export function useClassrooms() {
  return useQuery({
    queryKey: classroomKeys.all,
    queryFn: () => getJson<ClassroomsResponse>('/classrooms'),
  })
}

export function useCreateClassroom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (name: string) => sendJson<Classroom>('POST', '/classrooms', { name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: classroomKeys.all }),
  })
}

export function useRenameClassroom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      sendJson<Classroom>('PUT', `/classrooms/${id}`, { name }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: classroomKeys.all }),
  })
}

export function useRemoveClassroom() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => sendJson<unknown>('DELETE', `/classrooms/${id}`),
    // Os assignments da turma saem junto, então a lista deles também envelhece
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: classroomKeys.all }),
        queryClient.invalidateQueries({ queryKey: assignmentKeys.all }),
      ]),
  })
}
