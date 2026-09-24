import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { formatCount } from '../../../lib/format'
import { useRemoveClassroom, type ClassroomSummary } from '../api/classrooms'
import './RemoveClassroomDialog.css'

interface RemoveClassroomDialogProps {
  // Com a turma o diálogo está aberto, e sem ela está fechado
  classroom?: ClassroomSummary
  onClose: () => void
}

export function RemoveClassroomDialog({ classroom, onClose }: RemoveClassroomDialogProps) {
  return (
    <Dialog
      open={classroom != null}
      onClose={onClose}
      title={classroom ? `Excluir ${classroom.name}?` : ''}
      tone="danger"
    >
      {classroom ? <RemoveClassroomConfirmation classroom={classroom} onDone={onClose} /> : null}
    </Dialog>
  )
}

function RemoveClassroomConfirmation({
  classroom,
  onDone,
}: {
  classroom: ClassroomSummary
  onDone: () => void
}) {
  const remove = useRemoveClassroom()
  return (
    <>
      <DialogBody>
        <p>{consequence(classroom)} Não dá para desfazer.</p>
        {remove.isError ? (
          <p role="alert" className="remove-classroom__error">
            Não foi possível excluir. Verifique se a API está no ar e tente de novo.
          </p>
        ) : null}
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button
          variant="destructive"
          disabled={remove.isPending}
          onClick={() => remove.mutate(classroom.id, { onSuccess: onDone })}
        >
          Excluir turma
        </Button>
      </DialogFooter>
    </>
  )
}

// O que sai junto com a turma, dito antes de confirmar
function consequence(classroom: ClassroomSummary) {
  if (classroom.problem_count === 0) return 'A turma ainda não tem dados importados.'
  const problems = `${formatCount(classroom.problem_count)} ${classroom.problem_count === 1 ? 'problema' : 'problemas'}`
  return `Saem junto ${problems}, os conceitos e os modelos treinados dela.`
}
