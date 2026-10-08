import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { REOPEN_APPROVAL_NOTICE, type CellClickOutcome } from '../knowledgeComponents'

// O clique na célula que espera o aviso, guardado pelos ids até o professor seguir ou cancelar
export type PendingCellEdit = {
  action: Extract<CellClickOutcome, 'link' | 'unlink'>
  kcId: number
  problemId: number
}

interface ReopenApprovalDialogProps {
  edit?: PendingCellEdit
  // Com o pedido no ar o aviso fica aberto e sem clique, para o clique não cair na matriz embaixo
  isSending: boolean
  onConfirm: (edit: PendingCellEdit) => void
  onClose: () => void
}

// Neutro, porque não é exclusão, e a ação de seguir diz o que o clique faz
export function ReopenApprovalDialog({
  edit,
  isSending,
  onConfirm,
  onClose,
}: ReopenApprovalDialogProps) {
  return (
    <Dialog
      open={edit != null}
      onClose={onClose}
      title="Editar os conceitos aprovados?"
      dismissible={!isSending}
    >
      {edit ? (
        <>
          <DialogBody>
            <p>{REOPEN_APPROVAL_NOTICE}</p>
            <p>O exercício volta a rascunho, e você aprova de novo quando terminar.</p>
          </DialogBody>
          <DialogFooter>
            <Button variant="secondary" disabled={isSending} onClick={onClose}>
              Cancelar
            </Button>
            <Button variant="primary" disabled={isSending} onClick={() => onConfirm(edit)}>
              {edit.action === 'link' ? 'Ligar conceito' : 'Tirar conceito'}
            </Button>
          </DialogFooter>
        </>
      ) : null}
    </Dialog>
  )
}
