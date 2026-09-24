import { Badge } from '../../../components/ui/Badge'
import type { ClassroomStatus } from '../api/classrooms'

const LABEL: Record<ClassroomStatus, string> = {
  awaiting_data: 'Aguardando dados',
  in_progress: 'Em andamento',
  trained: 'Modelo treinado',
}

// Só a turma com modelo treinado ganha o azul suave, as outras ficam neutras
export function ClassroomStatusBadge({ status }: { status: ClassroomStatus }) {
  return <Badge tone={status === 'trained' ? 'accent' : 'neutral'}>{LABEL[status]}</Badge>
}
