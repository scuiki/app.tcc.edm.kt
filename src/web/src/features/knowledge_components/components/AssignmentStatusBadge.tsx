import { Badge } from '../../../components/ui/Badge'
import type { AssignmentStatus } from '../../assignments/api/useAssignments'
import { ASSIGNMENT_STATUS_LABEL } from '../knowledgeComponents'

// Só o modelo treinado ganha o azul suave, as outras situações ficam neutras
export function AssignmentStatusBadge({ status }: { status: AssignmentStatus | null }) {
  if (!status) return null
  return (
    <Badge tone={status === 'trained' ? 'accent' : 'neutral'}>
      {ASSIGNMENT_STATUS_LABEL[status]}
    </Badge>
  )
}
