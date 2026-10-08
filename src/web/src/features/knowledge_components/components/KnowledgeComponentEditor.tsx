import { useRef, useState } from 'react'
import { Blocks, Check, FileCode, Plus } from 'lucide-react'

import { OutcomeMessage } from '../../../components/OutcomeMessage'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { Tabs, type TabItem } from '../../../components/ui/Tabs'
import type { AssignmentStatus } from '../../assignments/api/useAssignments'
import {
  useApproveKnowledgeComponents,
  useLinkKnowledgeComponent,
  useUnlinkKnowledgeComponent,
  type ProblemKnowledgeComponents,
} from '../api/knowledgeComponents'
import {
  cellClickOutcomeOf,
  editErrorText,
  isEditable,
  knowledgeComponentsOf,
  problemsOnlyMarkedBy,
  problemsWithoutKnowledgeComponent,
  stableKnowledgeComponentOrder,
} from '../knowledgeComponents'
import { KnowledgeComponentMatrix } from './KnowledgeComponentMatrix'
import { NewKnowledgeComponentDialog } from './NewKnowledgeComponentDialog'
import { ProblemStatementsTable } from './ProblemStatementsTable'
import { RemoveKnowledgeComponentDialog } from './RemoveKnowledgeComponentDialog'
import { RenameKnowledgeComponentDialog } from './RenameKnowledgeComponentDialog'
import { ReopenApprovalDialog, type PendingCellEdit } from './ReopenApprovalDialog'
import { UnlinkKnowledgeComponentDialog, type UnlinkTarget } from './UnlinkKnowledgeComponentDialog'
import './KnowledgeComponentEditor.css'

type EditorTab = 'matrix' | 'problems'

const TABS: TabItem<EditorTab>[] = [
  { key: 'matrix', label: 'Conceitos por problema', icon: Blocks },
  { key: 'problems', label: 'Problemas', icon: FileCode },
]

// Um diálogo por vez, com o conceito e o problema pelo id, nunca uma cópia que envelhece
type EditorDialog =
  | { kind: 'closed' }
  | { kind: 'new' }
  | { kind: 'rename' | 'remove'; kcId: number }
  | { kind: 'unlink'; target: UnlinkTarget }
  | { kind: 'reopen'; edit: PendingCellEdit; isSending: boolean }

const CLOSED: EditorDialog = { kind: 'closed' }

const cellOf = (kcId: number, problemId: number) => `${kcId}:${problemId}`

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
  const [tab, setTab] = useState<EditorTab>('matrix')
  const [dialog, setDialog] = useState<EditorDialog>(CLOSED)
  const link = useLinkKnowledgeComponent(assignmentId)
  const unlink = useUnlinkKnowledgeComponent(assignmentId)
  const approve = useApproveKnowledgeComponents(assignmentId)
  // As células com um pedido no ar, para o clique duplo não mandar o mesmo pedido duas vezes
  const pendingCells = useRef(new Set<string>())
  const editable = isEditable(status)
  // A primeira edição dos aprovados volta o exercício a rascunho, e a recarga traz a situação nova
  const reopensApproval = status === 'kc_approved'
  const knowledgeComponents = knowledgeComponentsOf(problems)

  // A ordem da primeira carga fica nas recargas, porque a linha que pula sob o mouse desorienta
  const [order, setOrder] = useState(() => stableKnowledgeComponentOrder([], knowledgeComponents))
  const nextOrder = stableKnowledgeComponentOrder(order, knowledgeComponents)
  if (nextOrder !== order) setOrder(nextOrder)
  const byId = new Map(knowledgeComponents.map((kc) => [kc.id, kc]))
  const rows = nextOrder.map((id) => byId.get(id)!)

  const kcOfDialog =
    dialog.kind === 'rename' || dialog.kind === 'remove' ? byId.get(dialog.kcId) : undefined
  const canApprove =
    status === 'kc_draft' && problemsWithoutKnowledgeComponent(problems).length === 0
  const close = () => setDialog(CLOSED)

  // Uma mensagem de erro por vez, a da última ação
  function clearErrors() {
    link.reset()
    unlink.reset()
    approve.reset()
  }

  // O clique direto e o que passou pelo aviso de reabrir chegam aqui, e a trava vale para os dois
  async function editCell({ action, kcId, problemId }: PendingCellEdit) {
    const cell = cellOf(kcId, problemId)
    if (pendingCells.current.has(cell)) return
    clearErrors()
    const mutation = action === 'link' ? link : unlink
    pendingCells.current.add(cell)
    try {
      await mutation.mutateAsync({ kcId, problemId })
    } catch {
      // O erro fica no estado da mutação, que a mensagem do cartão já mostra
    } finally {
      pendingCells.current.delete(cell)
    }
  }

  function handleCellClick(kcId: number, problemId: number) {
    if (pendingCells.current.has(cellOf(kcId, problemId))) return
    const outcome = cellClickOutcomeOf(kcId, problemId, problems)
    if (outcome === 'link' || outcome === 'unlink') {
      const edit = { action: outcome, kcId, problemId }
      if (reopensApproval) setDialog({ kind: 'reopen', edit, isSending: false })
      else editCell(edit)
      return
    }
    // A recusa não muda nada, então não leva o aviso de reabrir
    const kcName = byId.get(kcId)?.name ?? ''
    setDialog({ kind: 'unlink', target: { kcId, kcName, problemId, kind: outcome } })
  }

  // O aviso fica aberto até o pedido voltar, e um erro vai para a mensagem do cartão
  async function handleReopenConfirm(edit: PendingCellEdit) {
    // O segundo clique de um clique duplo não manda outro pedido nem fecha o aviso antes da hora
    if (pendingCells.current.has(cellOf(edit.kcId, edit.problemId))) return
    setDialog({ kind: 'reopen', edit, isSending: true })
    await editCell(edit)
    close()
  }

  function handleApprove() {
    clearErrors()
    approve.mutate()
  }

  const failure = link.isError
    ? { title: 'Não foi possível ligar o conceito', error: link.error }
    : unlink.isError
      ? { title: 'Não foi possível tirar o conceito', error: unlink.error }
      : approve.isError
        ? { title: 'Não foi possível aprovar os conceitos', error: approve.error }
        : null

  return (
    <>
      <Card footer={footerOf(status, tab)}>
        <Tabs
          items={TABS}
          active={tab}
          onChange={setTab}
          label="Conceitos do exercício"
          actions={
            tab === 'matrix' && editable ? (
              <>
                <Button
                  variant="secondary"
                  size="compact"
                  icon={Plus}
                  onClick={() => setDialog({ kind: 'new' })}
                >
                  Novo conceito
                </Button>
                <Button
                  variant="primary"
                  size="compact"
                  icon={Check}
                  disabled={!canApprove || approve.isPending}
                  onClick={handleApprove}
                >
                  Aprovar conceitos
                </Button>
              </>
            ) : null
          }
        />
        {failure ? (
          <div className="kc-editor__outcome">
            <OutcomeMessage tone="danger" title={failure.title}>
              {editErrorText(failure.error)}
            </OutcomeMessage>
          </div>
        ) : null}
        {tab === 'matrix' ? (
          <KnowledgeComponentMatrix
            problems={problems}
            knowledgeComponents={rows}
            onCellClick={editable ? handleCellClick : undefined}
            onRename={editable ? (kcId) => setDialog({ kind: 'rename', kcId }) : undefined}
            onRemove={editable ? (kcId) => setDialog({ kind: 'remove', kcId }) : undefined}
          />
        ) : (
          <ProblemStatementsTable problems={problems} />
        )}
      </Card>
      <NewKnowledgeComponentDialog
        assignmentId={assignmentId}
        open={dialog.kind === 'new'}
        problems={problems}
        knowledgeComponents={knowledgeComponents}
        reopensApproval={reopensApproval}
        onClose={close}
      />
      <RenameKnowledgeComponentDialog
        assignmentId={assignmentId}
        knowledgeComponent={dialog.kind === 'rename' ? kcOfDialog : undefined}
        reopensApproval={reopensApproval}
        onClose={close}
      />
      <RemoveKnowledgeComponentDialog
        assignmentId={assignmentId}
        knowledgeComponent={dialog.kind === 'remove' ? kcOfDialog : undefined}
        blockingProblemIds={
          dialog.kind === 'remove' ? problemsOnlyMarkedBy(dialog.kcId, problems) : []
        }
        reopensApproval={reopensApproval}
        onClose={close}
      />
      <UnlinkKnowledgeComponentDialog
        assignmentId={assignmentId}
        target={dialog.kind === 'unlink' ? dialog.target : undefined}
        reopensApproval={reopensApproval}
        onClose={close}
      />
      <ReopenApprovalDialog
        edit={dialog.kind === 'reopen' ? dialog.edit : undefined}
        isSending={dialog.kind === 'reopen' && dialog.isSending}
        onConfirm={handleReopenConfirm}
        onClose={close}
      />
    </>
  )
}

// A frase de apoio no rascunho, só na matriz, a de consulta no treinado e nada nos aprovados
function footerOf(status: AssignmentStatus | null, tab: EditorTab) {
  if (status === 'trained') {
    return 'Exercício treinado. Os conceitos ficam só para consulta, para não divergirem do modelo.'
  }
  if (status === 'kc_draft' && tab === 'matrix') {
    return 'Clique numa célula para ligar ou desligar o conceito do problema. Passe o mouse no número para ver o enunciado.'
  }
  return null
}
