import { Button } from '../../../components/ui/Button'
import { DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { listProblemIds } from '../knowledgeComponents'

// A recusa de quando algum problema ficaria sem conceito, que não entra no modelo
export function LeavesProblemEmpty({
  problemIds,
  action,
  onClose,
}: {
  problemIds: number[]
  action: 'remover' | 'tirar'
  onClose: () => void
}) {
  const subject =
    problemIds.length === 1
      ? `O problema ${problemIds[0]} ficaria sem nenhum conceito`
      : `Os problemas ${listProblemIds(problemIds)} ficariam sem nenhum conceito`
  return (
    <>
      <DialogBody>
        <p>
          {subject}, e um problema sem conceito não entra no modelo. Dê outro conceito a ele antes
          de {action} este.
        </p>
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onClose}>
          Fechar
        </Button>
      </DialogFooter>
    </>
  )
}
