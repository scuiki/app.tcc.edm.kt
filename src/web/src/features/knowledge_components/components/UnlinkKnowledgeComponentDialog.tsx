import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { useUnlinkKnowledgeComponent, type KnowledgeComponent } from '../api/knowledgeComponents'
import { editErrorText } from '../knowledgeComponents'
import { LeavesProblemEmpty } from './LeavesProblemEmpty'
import './KnowledgeComponentDialogs.css'

// Só abre nos dois casos que pedem atenção, e o resto o xis tira direto
export type UnlinkTarget = {
  kc: KnowledgeComponent
  problemId: number
  // refused quando o problema ficaria vazio, confirm quando é o último problema do conceito
  kind: 'refused' | 'confirm'
}

interface UnlinkKnowledgeComponentDialogProps {
  assignmentId: number
  target?: UnlinkTarget
  onClose: () => void
}

export function UnlinkKnowledgeComponentDialog({
  assignmentId,
  target,
  onClose,
}: UnlinkKnowledgeComponentDialogProps) {
  const title = !target
    ? ''
    : target.kind === 'refused'
      ? 'Não dá para tirar este conceito'
      : `Tirar ${target.kc.name} do problema ${target.problemId}?`
  return (
    <Dialog open={target != null} onClose={onClose} title={title} tone="danger">
      {target?.kind === 'refused' ? (
        <LeavesProblemEmpty problemIds={[target.problemId]} action="tirar" onClose={onClose} />
      ) : null}
      {target?.kind === 'confirm' ? (
        <UnlinkConfirmation assignmentId={assignmentId} target={target} onDone={onClose} />
      ) : null}
    </Dialog>
  )
}

function UnlinkConfirmation({
  assignmentId,
  target,
  onDone,
}: {
  assignmentId: number
  target: UnlinkTarget
  onDone: () => void
}) {
  const unlink = useUnlinkKnowledgeComponent(assignmentId)
  return (
    <>
      <DialogBody>
        <p>
          O problema {target.problemId} é o único que este conceito marca, então ele sai do
          exercício junto. Não dá para desfazer.
        </p>
        {unlink.isError ? (
          <p role="alert" className="kc-dialog__error">
            {editErrorText(unlink.error)}
          </p>
        ) : null}
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button
          variant="destructive"
          disabled={unlink.isPending}
          onClick={() =>
            unlink.mutate(
              { kcId: target.kc.id, problemId: target.problemId },
              { onSuccess: onDone },
            )
          }
        >
          Tirar conceito
        </Button>
      </DialogFooter>
    </>
  )
}
