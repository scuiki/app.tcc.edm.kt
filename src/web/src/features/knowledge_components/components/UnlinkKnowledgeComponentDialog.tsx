import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { useUnlinkKnowledgeComponent } from '../api/knowledgeComponents'
import { editErrorText } from '../knowledgeComponents'
import { LeavesProblemEmpty } from './LeavesProblemEmpty'
import { ReopenApprovalNotice } from './ReopenApprovalNotice'
import './KnowledgeComponentDialogs.css'

// Só abre nos dois casos que pedem atenção, e nos outros a célula desliga direto ou pelo aviso
export type UnlinkTarget = {
  kcId: number
  // O nome fica guardado porque o conceito some da resposta quando sai do exercício
  kcName: string
  problemId: number
  // refused quando o problema ficaria vazio, confirm quando é o último problema do conceito
  kind: 'refused' | 'confirm'
}

interface UnlinkKnowledgeComponentDialogProps {
  assignmentId: number
  target?: UnlinkTarget
  // Nos conceitos aprovados a confirmação leva a linha do aviso de reabrir, e a recusa não
  reopensApproval: boolean
  onClose: () => void
}

export function UnlinkKnowledgeComponentDialog({
  assignmentId,
  target,
  reopensApproval,
  onClose,
}: UnlinkKnowledgeComponentDialogProps) {
  const title = !target
    ? ''
    : target.kind === 'refused'
      ? 'Não dá para tirar este conceito'
      : `Tirar ${target.kcName} do problema ${target.problemId}?`
  return (
    <Dialog open={target != null} onClose={onClose} title={title} tone="danger">
      {target?.kind === 'refused' ? (
        <LeavesProblemEmpty problemIds={[target.problemId]} action="tirar" onClose={onClose} />
      ) : null}
      {target?.kind === 'confirm' ? (
        <UnlinkConfirmation
          assignmentId={assignmentId}
          target={target}
          reopensApproval={reopensApproval}
          onDone={onClose}
        />
      ) : null}
    </Dialog>
  )
}

function UnlinkConfirmation({
  assignmentId,
  target,
  reopensApproval,
  onDone,
}: {
  assignmentId: number
  target: UnlinkTarget
  reopensApproval: boolean
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
        <ReopenApprovalNotice reopensApproval={reopensApproval} />
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
            unlink.mutate({ kcId: target.kcId, problemId: target.problemId }, { onSuccess: onDone })
          }
        >
          Tirar conceito
        </Button>
      </DialogFooter>
    </>
  )
}
