import { Inbox } from 'lucide-react'

import { Breadcrumb } from '../../../components/Breadcrumb'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyState, ErrorState, LoadingState } from '../../../components/states/states'
import { Badge } from '../../../components/ui/Badge'
import { Card } from '../../../components/ui/Card'
import { formatCount, formatDate } from '../../../lib/format'
import { assignmentPath, classroomImportPath } from '../../../lib/paths'
import {
  ASSIGNMENT_STATUS_LABEL,
  useAssignmentContext,
  type AssignmentSummary,
} from '../../assignments/api/useAssignmentContext'
import './ClassroomPage.css'

// A página de uma turma, com os exercícios dela em cartões e o caminho para cada tela
export function ClassroomPage({ classroomId }: { classroomId?: number }) {
  const context = useAssignmentContext(classroomId)
  if (context.isPending) return <LoadingState label="Carregando a turma…" />
  if (context.isError) return <ErrorState />
  const { classroom, assignments } = context
  if (!classroom) {
    return (
      <Card title="Turma não encontrada">
        <EmptyState
          text="Esta turma não existe mais ou o endereço está errado."
          action={<a href="#/classrooms">Ir para Turmas</a>}
        />
      </Card>
    )
  }
  return (
    <>
      <Breadcrumb items={[{ label: 'Turmas', href: '/classrooms' }, { label: classroom.name }]} />
      <PageHeader
        title={classroom.name}
        description={`${formatCount(classroom.student_count)} alunos · ${formatCount(classroom.problem_count)} problemas · criada em ${formatDate(classroom.created_at)}`}
      />
      <Card
        title="Exercícios"
        footer={
          <a href={`#${classroomImportPath(classroom.id)}`}>Importar dados para esta turma</a>
        }
      >
        {assignments.length === 0 ? (
          <EmptyState
            icon={Inbox}
            title="Nenhum exercício ainda"
            text="Os exercícios aparecem depois de importar os dados ProgSnap2 da turma."
            action={<a href={`#${classroomImportPath(classroom.id)}`}>Importar dados</a>}
          />
        ) : (
          <ul className="assignment-cards">
            {assignments.map((assignment) => (
              <AssignmentCard
                key={assignment.id}
                classroomId={classroom.id}
                assignment={assignment}
              />
            ))}
          </ul>
        )}
      </Card>
    </>
  )
}

function AssignmentCard({
  classroomId,
  assignment,
}: {
  classroomId: number
  assignment: AssignmentSummary
}) {
  const status = assignment.status
  return (
    <li className="assignment-card">
      {status ? (
        <Badge tone={status === 'trained' ? 'accent' : 'neutral'}>
          {ASSIGNMENT_STATUS_LABEL[status]}
        </Badge>
      ) : null}
      <span className="assignment-card__name">{assignment.name}</span>
      <span className="assignment-card__links">
        <a href={`#${assignmentPath(classroomId, assignment.id, 'knowledge-components')}`}>
          Conceitos
        </a>
        <a href={`#${assignmentPath(classroomId, assignment.id, 'analysis')}`}>Análise</a>
      </span>
    </li>
  )
}
