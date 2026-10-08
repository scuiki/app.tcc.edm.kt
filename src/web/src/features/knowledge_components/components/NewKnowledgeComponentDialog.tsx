import { useId, useState, type FormEvent } from 'react'
import { CircleAlert } from 'lucide-react'

import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { TextField } from '../../../components/ui/TextField'
import { formatCount } from '../../../lib/format'
import {
  useCreateKnowledgeComponent,
  type ProblemKnowledgeComponents,
} from '../api/knowledgeComponents'
import { editErrorText, normalizedName, type KnowledgeComponentUsage } from '../knowledgeComponents'
import { ReopenApprovalNotice } from './ReopenApprovalNotice'
import './KnowledgeComponentDialogs.css'

interface NewKnowledgeComponentDialogProps {
  assignmentId: number
  open: boolean
  problems: ProblemKnowledgeComponents[]
  knowledgeComponents: KnowledgeComponentUsage[]
  // Nos conceitos aprovados o formulário leva a linha do aviso de reabrir, acima dos botões
  reopensApproval: boolean
  onClose: () => void
}

// O formulário só existe aberto, então o nome e as caixas nascem vazios a cada abertura
export function NewKnowledgeComponentDialog({
  assignmentId,
  open,
  problems,
  knowledgeComponents,
  reopensApproval,
  onClose,
}: NewKnowledgeComponentDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} title="Novo conceito">
      <NewKnowledgeComponentForm
        assignmentId={assignmentId}
        problems={problems}
        knowledgeComponents={knowledgeComponents}
        reopensApproval={reopensApproval}
        onDone={onClose}
      />
    </Dialog>
  )
}

interface NewKnowledgeComponentFormProps {
  assignmentId: number
  problems: ProblemKnowledgeComponents[]
  knowledgeComponents: KnowledgeComponentUsage[]
  reopensApproval: boolean
  onDone: () => void
}

function NewKnowledgeComponentForm({
  assignmentId,
  problems,
  knowledgeComponents,
  reopensApproval,
  onDone,
}: NewKnowledgeComponentFormProps) {
  const hintId = useId()
  const [name, setName] = useState('')
  const [markedIds, setMarkedIds] = useState<number[]>([])
  const create = useCreateKnowledgeComponent(assignmentId)
  const trimmed = name.trim()
  const isTaken =
    trimmed !== '' &&
    knowledgeComponents.some((kc) => normalizedName(kc.name) === normalizedName(trimmed))
  const canCreate = trimmed !== '' && !isTaken && markedIds.length > 0 && !create.isPending

  function toggle(problemId: number) {
    setMarkedIds((ids) =>
      ids.includes(problemId) ? ids.filter((id) => id !== problemId) : [...ids, problemId],
    )
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!canCreate) return
    // Na ordem dos problemas, e não na ordem dos cliques
    const problemIds = problems
      .map((problem) => problem.problem_id)
      .filter((id) => markedIds.includes(id))
    create.mutate({ name: trimmed, problemIds }, { onSuccess: onDone })
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <DialogBody>
        <TextField
          label="Nome"
          required
          autoFocus
          autoComplete="off"
          value={name}
          onChange={(event) => setName(event.target.value)}
          error={isTaken ? 'Já existe um conceito com este nome.' : undefined}
        />
        <fieldset className="kc-new__problems" aria-describedby={hintId}>
          <legend className="field__label">
            Problemas
            <span className="field__required" aria-hidden="true">
              {' '}
              *
            </span>
          </legend>
          <span id={hintId} className="field__hint">
            Marque pelo menos um problema. O conceito entra só nos marcados.
          </span>
          <div className="kc-new__items">
            {problems.map((problem) => (
              <ProblemOption
                key={problem.problem_id}
                problem={problem}
                checked={markedIds.includes(problem.problem_id)}
                onToggle={() => toggle(problem.problem_id)}
              />
            ))}
          </div>
        </fieldset>
        <p className="kc-dialog__note">O conceito novo nasce sem estrelas, porque o nome é seu.</p>
        <ReopenApprovalNotice reopensApproval={reopensApproval} />
        {create.isError ? (
          <p role="alert" className="kc-dialog__error">
            {editErrorText(create.error)}
          </p>
        ) : null}
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" variant="primary" disabled={!canCreate}>
          Criar
        </Button>
      </DialogFooter>
    </form>
  )
}

interface ProblemOptionProps {
  problem: ProblemKnowledgeComponents
  checked: boolean
  onToggle: () => void
}

// O nome da caixa é só o número, e o enunciado e a contagem ficam na descrição dela
function ProblemOption({ problem, checked, onToggle }: ProblemOptionProps) {
  const id = useId()
  const count = problem.knowledge_components.length
  return (
    <label className="kc-new__item">
      <input
        type="checkbox"
        checked={checked}
        onChange={onToggle}
        aria-labelledby={`${id}-number`}
        aria-describedby={`${id}-statement ${id}-count`}
      />
      <span className="kc-new__text">
        <span id={`${id}-number`} className="kc-new__number num">
          {problem.problem_id}
        </span>
        <span id={`${id}-statement`} className="kc-new__statement">
          {problem.statement ?? <span className="kc-new__missing">sem enunciado</span>}
        </span>
      </span>
      {count === 0 ? (
        <span id={`${id}-count`} className="kc-new__count kc-new__count--empty">
          <CircleAlert size={13} aria-hidden="true" />
          sem conceito
        </span>
      ) : (
        <span id={`${id}-count`} className="kc-new__count">
          {formatCount(count)} {count === 1 ? 'conceito' : 'conceitos'}
        </span>
      )}
    </label>
  )
}
