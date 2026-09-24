import { useMutation, useQueryClient } from '@tanstack/react-query'

import { sendForm, sendJson } from '../../../http/client'
import type { Schema } from '../../../http/types'
import { assignmentKeys } from '../../assignments/api/useAssignments'
import { classroomKeys } from '../../classrooms/api/classrooms'

export type DetectedUpload = Schema<'UploadClassroomDatasetResponseDTO'>
export type ClassroomImportReport = Schema<'ImportClassroomDatasetResponseDTO'>
export type ImportCheck = Schema<'ImportCheckDTO'>
export type AssignmentTrainability = Schema<'AssignmentTrainabilityDTO'>
type ImportRequest = Schema<'ImportClassroomDatasetDTO'>

// O mesmo teto do backend, conferido antes de enviar para não subir um arquivo que será recusado
export const MAX_UPLOAD_BYTES = 512 * 1024 * 1024

export class UploadTooLargeError extends Error {}

export function useUploadClassroomDataset() {
  return useMutation({
    mutationFn: async ({ classroomId, file }: { classroomId: number; file: File }) => {
      if (file.size > MAX_UPLOAD_BYTES) throw new UploadTooLargeError()
      const form = new FormData()
      form.append('classroom_id', String(classroomId))
      form.append('file', file)
      return sendForm<DetectedUpload>('/classroom-imports', form)
    },
  })
}

export function useImportClassroomDataset() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (request: ImportRequest) =>
      sendJson<ClassroomImportReport>('POST', '/classroom-imports/process', request),
    // A turma ganha problemas, alunos e exercícios, então as duas listas envelhecem
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: classroomKeys.all }),
        queryClient.invalidateQueries({ queryKey: assignmentKeys.all }),
      ]),
  })
}
