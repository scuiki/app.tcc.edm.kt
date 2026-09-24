import { Users } from 'lucide-react'

import { Card } from '../../../components/ui/Card'
import { formatDateTime } from '../../../lib/format'
import type { ClassroomSummary } from '../api/classrooms'
import './RecentActivityCard.css'

const MAX_ITEMS = 5

// A única data que a api guarda é a de criação da turma, então a atividade é só essa
function mostRecent(classrooms: ClassroomSummary[]) {
  return [...classrooms]
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .slice(0, MAX_ITEMS)
}

export function RecentActivityCard({ classrooms }: { classrooms: ClassroomSummary[] }) {
  return (
    <Card title="Atividade recente">
      <ol className="activity">
        {mostRecent(classrooms).map((classroom) => (
          <li key={classroom.id} className="activity__item">
            <span className="activity__icon">
              <Users size={15} aria-hidden="true" />
            </span>
            <div className="activity__text">
              <span>
                <strong>{classroom.name}</strong> foi criada
              </span>
              <span className="activity__time mono">{formatDateTime(classroom.created_at)}</span>
            </div>
          </li>
        ))}
      </ol>
    </Card>
  )
}
