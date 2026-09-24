import { useState, type FormEvent } from 'react'

import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { TextField } from '../../../components/ui/TextField'
import { isApiError } from '../../../http/client'
import { useCreateClassroom, useRenameClassroom, type ClassroomSummary } from '../api/classrooms'

// O mesmo limite do backend
const MAX_NAME_LENGTH = 120

interface ClassroomNameDialogProps {
  open: boolean
  onClose: () => void
  // Com a turma, o diálogo renomeia, e sem ela cria uma nova
  classroom?: ClassroomSummary
}

export function ClassroomNameDialog({ open, onClose, classroom }: ClassroomNameDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} title={classroom ? 'Renomear turma' : 'Nova turma'}>
      <ClassroomNameForm key={classroom?.id ?? 'new'} classroom={classroom} onDone={onClose} />
    </Dialog>
  )
}

interface ClassroomNameFormProps {
  classroom?: ClassroomSummary
  onDone: () => void
}

// Monta a cada abertura do diálogo, então o valor inicial basta, sem effect de reset
function ClassroomNameForm({ classroom, onDone }: ClassroomNameFormProps) {
  const [name, setName] = useState(classroom?.name ?? '')
  const create = useCreateClassroom()
  const rename = useRenameClassroom()
  const mutation = classroom ? rename : create

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (classroom) rename.mutate({ id: classroom.id, name: trimmed }, { onSuccess: onDone })
    else create.mutate(trimmed, { onSuccess: onDone })
  }

  function handleNameChange(value: string) {
    setName(value)
    // A recusa anterior some assim que o professor corrige o nome
    if (mutation.isError) mutation.reset()
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <DialogBody>
        <TextField
          label="Nome"
          required
          autoFocus
          maxLength={MAX_NAME_LENGTH}
          value={name}
          onChange={(event) => handleNameChange(event.target.value)}
          hint="Ex.: Algoritmos I — 2026/2. Você importa os dados depois."
          error={errorMessage(mutation.error)}
        />
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" variant="primary" disabled={!name.trim() || mutation.isPending}>
          {classroom ? 'Salvar' : 'Criar'}
        </Button>
      </DialogFooter>
    </form>
  )
}

function errorMessage(error: Error | null): string | undefined {
  if (!error) return undefined
  if (isApiError(error, 409)) return 'Você já tem uma turma com esse nome.'
  return 'Não foi possível salvar. Verifique se a API está no ar e tente de novo.'
}
