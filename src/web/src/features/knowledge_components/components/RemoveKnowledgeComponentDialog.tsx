import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { useRemoveKnowledgeComponent } from '../api/knowledgeComponents'
import {
  editErrorText,
  listProblemIds,
  problemCount,
  type KnowledgeComponentUsage,
} from '../knowledgeComponents'
import { LeavesProblemEmpty } from './LeavesProblemEmpty'
import './KnowledgeComponentDialogs.css'

interface RemoveKnowledgeComponentDialogProps {
  assignmentId: number
  knowledgeComponent?: KnowledgeComponentUsage
  // Os problemas em que ele é o único conceito, e que por isso barram a remoção
  blockingProblemIds: number[]
  onClose: () => void
}

export function RemoveKnowledgeComponentDialog({
  assignmentId,
  knowledgeComponent,
  blockingProblemIds,
  onClose,
}: RemoveKnowledgeComponentDialogProps) {
  const isBlocked = blockingProblemIds.length > 0
  const title = !knowledgeComponent
    ? ''
    : isBlocked
      ? 'Não dá para remover este conceito'
      : `Remover ${knowledgeComponent.name}?`
  return (
    <Dialog open={knowledgeComponent != null} onClose={onClose} title={title} tone="danger">
      {knowledgeComponent && isBlocked ? (
        <LeavesProblemEmpty problemIds={blockingProblemIds} action="remover" onClose={onClose} />
      ) : null}
      {knowledgeComponent && !isBlocked ? (
        <RemoveConfirmation assignmentId={assignmentId} kc={knowledgeComponent} onDone={onClose} />
      ) : null}
    </Dialog>
  )
}

function RemoveConfirmation({
  assignmentId,
  kc,
  onDone,
}: {
  assignmentId: number
  kc: KnowledgeComponentUsage
  onDone: () => void
}) {
  const remove = useRemoveKnowledgeComponent(assignmentId)
  return (
    <>
      <DialogBody>
        <p>
          Ele marca {problemCount(kc.problemIds.length)}: {listProblemIds(kc.problemIds)}. A remoção
          vale para o exercício inteiro e não pode ser desfeita.
        </p>
        {remove.isError ? (
          <p role="alert" className="kc-dialog__error">
            {editErrorText(remove.error)}
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
          onClick={() => remove.mutate(kc.id, { onSuccess: onDone })}
        >
          Remover conceito
        </Button>
      </DialogFooter>
    </>
  )
}
