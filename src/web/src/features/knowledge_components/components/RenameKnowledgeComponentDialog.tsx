import { useState, type FormEvent } from 'react'

import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { TextField } from '../../../components/ui/TextField'
import { useRenameKnowledgeComponent } from '../api/knowledgeComponents'
import {
  editErrorText,
  listProblemIds,
  problemCount,
  type KnowledgeComponentUsage,
} from '../knowledgeComponents'
import './KnowledgeComponentDialogs.css'

interface RenameKnowledgeComponentDialogProps {
  assignmentId: number
  knowledgeComponent?: KnowledgeComponentUsage
  onClose: () => void
}

export function RenameKnowledgeComponentDialog({
  assignmentId,
  knowledgeComponent,
  onClose,
}: RenameKnowledgeComponentDialogProps) {
  return (
    <Dialog open={knowledgeComponent != null} onClose={onClose} title="Editar conceito">
      {knowledgeComponent ? (
        <RenameForm assignmentId={assignmentId} kc={knowledgeComponent} onDone={onClose} />
      ) : null}
    </Dialog>
  )
}

function RenameForm({
  assignmentId,
  kc,
  onDone,
}: {
  assignmentId: number
  kc: KnowledgeComponentUsage
  onDone: () => void
}) {
  const [name, setName] = useState(kc.name)
  const rename = useRenameKnowledgeComponent(assignmentId)
  const trimmed = name.trim()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    rename.mutate({ kcId: kc.id, name: trimmed }, { onSuccess: onDone })
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <DialogBody>
        <TextField
          label="Nome"
          required
          autoFocus
          value={name}
          onChange={(event) => setName(event.target.value)}
          error={rename.isError ? editErrorText(rename.error) : undefined}
        />
        <p className="kc-dialog__note">
          Este conceito marca {problemCount(kc.problemIds.length)}: {listProblemIds(kc.problemIds)}.
          O nome novo passa a valer em todos eles.
        </p>
        {kc.is_generated_by_llm ? (
          <p className="kc-dialog__note">
            O nome atual veio do modelo de linguagem. Ao salvar, o nome passa a ser seu e as
            estrelas saem.
          </p>
        ) : null}
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button
          type="submit"
          variant="primary"
          disabled={!trimmed || trimmed === kc.name || rename.isPending}
        >
          Salvar
        </Button>
      </DialogFooter>
    </form>
  )
}
