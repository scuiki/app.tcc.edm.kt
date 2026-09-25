import { useState } from 'react'

import { OutcomeMessage } from '../../../components/OutcomeMessage'
import type { AssignmentStatus } from '../../assignments/api/useAssignments'
import {
  useUnlinkKnowledgeComponent,
  type KnowledgeComponent,
  type ProblemKnowledgeComponents,
} from '../api/knowledgeComponents'
import {
  editErrorText,
  isEditable,
  knowledgeComponentsOf,
  problemsOnlyMarkedBy,
} from '../knowledgeComponents'
import { AddKnowledgeComponentDialog } from './AddKnowledgeComponentDialog'
import { KnowledgeComponentsCard } from './KnowledgeComponentsCard'
import { MergeKnowledgeComponentsDialog } from './MergeKnowledgeComponentsDialog'
import { ProblemsCard } from './ProblemsCard'
import { RemoveKnowledgeComponentDialog } from './RemoveKnowledgeComponentDialog'
import { RenameKnowledgeComponentDialog } from './RenameKnowledgeComponentDialog'
import { UnlinkKnowledgeComponentDialog, type UnlinkTarget } from './UnlinkKnowledgeComponentDialog'
import './KnowledgeComponentEditor.css'

// Um diálogo por vez, com o conceito e o problema pelo id, nunca uma cópia que envelhece
type EditorDialog =
  | { kind: 'closed' }
  | { kind: 'add'; problemId: number }
  | { kind: 'rename' | 'merge' | 'remove'; kcId: number }
  | { kind: 'unlink'; target: UnlinkTarget }

const CLOSED: EditorDialog = { kind: 'closed' }

interface KnowledgeComponentEditorProps {
  assignmentId: number
  status: AssignmentStatus | null
  problems: ProblemKnowledgeComponents[]
}

export function KnowledgeComponentEditor({
  assignmentId,
  status,
  problems,
}: KnowledgeComponentEditorProps) {
  const [dialog, setDialog] = useState<EditorDialog>(CLOSED)
  const unlink = useUnlinkKnowledgeComponent(assignmentId)
  const editable = isEditable(status)
  const knowledgeComponents = knowledgeComponentsOf(problems)
  const kcOfDialog =
    dialog.kind === 'rename' || dialog.kind === 'merge' || dialog.kind === 'remove'
      ? knowledgeComponents.find((kc) => kc.id === dialog.kcId)
      : undefined
  const close = () => setDialog(CLOSED)

  // O xis tira direto, e só pede atenção quando o problema ficaria vazio ou o conceito sairia junto
  function handleUnlink(kc: KnowledgeComponent, problemId: number) {
    const problem = problems.find((candidate) => candidate.problem_id === problemId)
    const usage = knowledgeComponents.find((candidate) => candidate.id === kc.id)
    if (problem?.knowledge_components.length === 1) {
      setDialog({ kind: 'unlink', target: { kc, problemId, kind: 'refused' } })
    } else if (usage?.problemIds.length === 1) {
      setDialog({ kind: 'unlink', target: { kc, problemId, kind: 'confirm' } })
    } else {
      unlink.mutate({ kcId: kc.id, problemId })
    }
  }

  return (
    <>
      {status === 'trained' ? (
        <p className="kc-editor__notice">
          Este exercício já tem modelo treinado. Os conceitos ficam só para consulta, para não
          divergirem do modelo publicado.
        </p>
      ) : null}
      {status === 'kc_approved' ? (
        <p className="kc-editor__notice kc-editor__notice--approved">
          Conceitos aprovados. Mexer em qualquer conceito agora devolve o exercício para rascunho e
          pede nova aprovação.
        </p>
      ) : null}
      {unlink.isError ? (
        <OutcomeMessage tone="danger" title="Não foi possível tirar o conceito">
          {editErrorText(unlink.error)}
        </OutcomeMessage>
      ) : null}
      <div className="kc-editor">
        <div className="kc-editor__problems">
          <ProblemsCard
            problems={problems}
            onUnlink={editable ? handleUnlink : undefined}
            onAdd={editable ? (problemId) => setDialog({ kind: 'add', problemId }) : undefined}
            isBusy={unlink.isPending}
          />
        </div>
        <div className="kc-editor__side">
          <KnowledgeComponentsCard
            knowledgeComponents={knowledgeComponents}
            problemTotal={problems.length}
            problemsWithoutKnowledgeComponent={
              problems.filter((problem) => problem.knowledge_components.length === 0).length
            }
            onRename={editable ? (kcId) => setDialog({ kind: 'rename', kcId }) : undefined}
            onMerge={editable ? (kcId) => setDialog({ kind: 'merge', kcId }) : undefined}
            onRemove={editable ? (kcId) => setDialog({ kind: 'remove', kcId }) : undefined}
            isBusy={unlink.isPending}
          />
        </div>
      </div>
      <AddKnowledgeComponentDialog
        assignmentId={assignmentId}
        problemId={dialog.kind === 'add' ? dialog.problemId : null}
        knowledgeComponents={knowledgeComponents}
        onClose={close}
      />
      <RenameKnowledgeComponentDialog
        assignmentId={assignmentId}
        knowledgeComponent={dialog.kind === 'rename' ? kcOfDialog : undefined}
        onClose={close}
      />
      <MergeKnowledgeComponentsDialog
        assignmentId={assignmentId}
        knowledgeComponent={dialog.kind === 'merge' ? kcOfDialog : undefined}
        knowledgeComponents={knowledgeComponents}
        onClose={close}
      />
      <RemoveKnowledgeComponentDialog
        assignmentId={assignmentId}
        knowledgeComponent={dialog.kind === 'remove' ? kcOfDialog : undefined}
        blockingProblemIds={
          dialog.kind === 'remove' ? problemsOnlyMarkedBy(dialog.kcId, problems) : []
        }
        onClose={close}
      />
      <UnlinkKnowledgeComponentDialog
        assignmentId={assignmentId}
        target={dialog.kind === 'unlink' ? dialog.target : undefined}
        onClose={close}
      />
    </>
  )
}
