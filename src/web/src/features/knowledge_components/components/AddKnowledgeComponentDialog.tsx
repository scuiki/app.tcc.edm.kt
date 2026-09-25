import { useId, useState, type FormEvent } from 'react'

import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { useCreateKnowledgeComponent, useLinkKnowledgeComponent } from '../api/knowledgeComponents'
import { editErrorText, problemCount, type KnowledgeComponentUsage } from '../knowledgeComponents'
import './KnowledgeComponentDialogs.css'

interface AddKnowledgeComponentDialogProps {
  assignmentId: number
  // Com o problema o diálogo está aberto, e sem ele está fechado
  problemId: number | null
  knowledgeComponents: KnowledgeComponentUsage[]
  onClose: () => void
}

export function AddKnowledgeComponentDialog({
  assignmentId,
  problemId,
  knowledgeComponents,
  onClose,
}: AddKnowledgeComponentDialogProps) {
  return (
    <Dialog open={problemId != null} onClose={onClose} title="Adicionar conceito">
      {problemId != null ? (
        <AddKnowledgeComponentForm
          assignmentId={assignmentId}
          problemId={problemId}
          knowledgeComponents={knowledgeComponents}
          onDone={onClose}
        />
      ) : null}
    </Dialog>
  )
}

// Ligar um conceito que já existe ou criar um novo com o nome digitado
type Choice = { kind: 'existing'; kcId: number } | { kind: 'new' } | null

function normalize(text: string) {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
    .trim()
}

interface AddKnowledgeComponentFormProps {
  assignmentId: number
  problemId: number
  knowledgeComponents: KnowledgeComponentUsage[]
  onDone: () => void
}

function AddKnowledgeComponentForm({
  assignmentId,
  problemId,
  knowledgeComponents,
  onDone,
}: AddKnowledgeComponentFormProps) {
  const searchId = useId()
  const [search, setSearch] = useState('')
  const [choice, setChoice] = useState<Choice>(null)
  const link = useLinkKnowledgeComponent(assignmentId)
  const create = useCreateKnowledgeComponent(assignmentId)
  const mutation = choice?.kind === 'new' ? create : link

  // Só os que ainda não marcam este problema, filtrados pelo que foi digitado
  const available = knowledgeComponents.filter((kc) => !kc.problemIds.includes(problemId))
  const matches = available.filter((kc) => normalize(kc.name).includes(normalize(search)))
  const typed = search.trim()
  const canCreate =
    typed !== '' && !knowledgeComponents.some((kc) => normalize(kc.name) === normalize(typed))

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (choice?.kind === 'existing') {
      link.mutate({ kcId: choice.kcId, problemId }, { onSuccess: onDone })
    } else if (choice?.kind === 'new' && canCreate) {
      create.mutate({ name: typed, problemId }, { onSuccess: onDone })
    }
  }

  function handleSearch(value: string) {
    setSearch(value)
    // O conceito novo leva o nome digitado, então mudar o texto desfaz a escolha dele
    if (choice?.kind === 'new') setChoice(null)
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <DialogBody>
        <p className="kc-dialog__subtitle">Problema {problemId}</p>
        <label htmlFor={searchId} className="kc-dialog__label">
          Buscar um conceito ou digitar um novo
        </label>
        <input
          id={searchId}
          type="text"
          className="kc-dialog__input"
          autoFocus
          value={search}
          onChange={(event) => handleSearch(event.target.value)}
        />
        <fieldset className="kc-options">
          <legend className="visually-hidden">Conceito para o problema {problemId}</legend>
          {matches.map((kc) => (
            <label
              key={kc.id}
              className={`kc-options__item${choice?.kind === 'existing' && choice.kcId === kc.id ? ' kc-options__item--chosen' : ''}`}
            >
              <input
                type="radio"
                name="knowledge-component"
                checked={choice?.kind === 'existing' && choice.kcId === kc.id}
                onChange={() => setChoice({ kind: 'existing', kcId: kc.id })}
              />
              <span className="kc-options__text">
                <span className="kc-options__name">{kc.name}</span>
                <span className="t-support">marca {problemCount(kc.problemIds.length)}</span>
              </span>
            </label>
          ))}
          {canCreate ? (
            <label
              className={`kc-options__item${choice?.kind === 'new' ? ' kc-options__item--chosen' : ''}`}
            >
              <input
                type="radio"
                name="knowledge-component"
                checked={choice?.kind === 'new'}
                onChange={() => setChoice({ kind: 'new' })}
              />
              <span className="kc-options__text">
                <span className="kc-options__name">Criar “{typed}”</span>
                <span className="t-support">um conceito novo, só neste problema por enquanto</span>
              </span>
            </label>
          ) : null}
          {matches.length === 0 && !canCreate ? (
            <p className="t-support">Digite o nome de um conceito para buscar ou criar.</p>
          ) : null}
        </fieldset>
        {mutation.isError ? (
          <p role="alert" className="kc-dialog__error">
            {editErrorText(mutation.error)}
          </p>
        ) : null}
      </DialogBody>
      <DialogFooter>
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" variant="primary" disabled={!choice || mutation.isPending}>
          Adicionar
        </Button>
      </DialogFooter>
    </form>
  )
}
