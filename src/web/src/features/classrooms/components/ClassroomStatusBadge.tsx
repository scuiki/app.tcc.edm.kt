import { Brain } from 'lucide-react'

import { Badge } from '../../../components/ui/Badge'
import type { ClassroomStatus } from '../api/classrooms'

const LABEL: Record<ClassroomStatus, string> = {
  awaiting_data: 'Aguardando dados',
  in_progress: 'Em andamento',
  trained: 'Treinado',
}

// Só a turma com modelo treinado ganha o azul e o cérebro, as outras ficam neutras e sem ícone
export function ClassroomStatusBadge({ status }: { status: ClassroomStatus }) {
  return status === 'trained' ? (
    <Badge tone="model" icon={Brain}>
      {LABEL[status]}
    </Badge>
  ) : (
    <Badge tone="neutral">{LABEL[status]}</Badge>
  )
}
