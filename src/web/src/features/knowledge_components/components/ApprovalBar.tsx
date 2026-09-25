import { PageActionBar } from '../../../components/PageActionBar'
import { Button } from '../../../components/ui/Button'
import type { AssignmentStatus } from '../../assignments/api/useAssignments'
import { useApproveKnowledgeComponents } from '../api/knowledgeComponents'
import { editErrorText } from '../knowledgeComponents'
import './KnowledgeComponentEditor.css'

interface ApprovalBarProps {
  assignmentId: number
  status: AssignmentStatus
  approvedCount: number
  assignmentCount: number
}

// A aprovação é o portão humano do processo e vale por exercício, sem o treino começar sem ela
export function ApprovalBar({
  assignmentId,
  status,
  approvedCount,
  assignmentCount,
}: ApprovalBarProps) {
  const approve = useApproveKnowledgeComponents(assignmentId)
  return (
    <PageActionBar
      message={`${approvedCount} de ${assignmentCount} exercícios aprovados. Aprovar libera o treino, e editar um conceito depois volta o exercício para rascunho.`}
    >
      {approve.isError ? (
        <span role="alert" className="kc-editor__error">
          {editErrorText(approve.error)}
        </span>
      ) : null}
      <Button
        variant="primary"
        disabled={status !== 'kc_draft' || approve.isPending}
        onClick={() => approve.mutate()}
      >
        {status === 'kc_approved' ? 'Exercício aprovado' : 'Aprovar este exercício'}
      </Button>
    </PageActionBar>
  )
}
