import { Breadcrumb } from '../../../components/Breadcrumb'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyState, ErrorState, LoadingState } from '../../../components/states/states'
import { Badge } from '../../../components/ui/Badge'
import { Card } from '../../../components/ui/Card'
import { classroomPath } from '../../../lib/paths'
import {
  assignmentStatusBadge,
  useAssignmentContext,
} from '../../assignments/api/useAssignmentContext'
import { ApprovalBar } from '../components/ApprovalBar'
import { AssignmentWorkspace } from '../components/AssignmentWorkspace'
import { isEditable } from '../knowledgeComponents'

const DESCRIPTION =
  'O modelo sugere os conceitos a partir das soluções corretas. Ajuste o que não bater com a sua disciplina e aprove para liberar o treino.'

interface KnowledgeComponentsPageProps {
  classroomId?: number
  assignmentId?: number
}

// O exercício vem do endereço; a tela só mostra os conceitos dele
export function KnowledgeComponentsPage({
  classroomId,
  assignmentId,
}: KnowledgeComponentsPageProps) {
  const context = useAssignmentContext(classroomId, assignmentId)
  if (context.isPending) return <LoadingState label="Carregando o exercício…" />
  if (context.isError) return <ErrorState />
  const { classroom, assignment, assignments } = context
  if (!classroom || !assignment) {
    return (
      <Card title="Exercício não encontrado">
        <EmptyState
          text="Este exercício não existe mais ou o endereço está errado."
          action={<a href="#/classrooms">Ir para Turmas</a>}
        />
      </Card>
    )
  }
  const approvedCount = assignments.filter(
    (candidate) => candidate.status === 'kc_approved' || candidate.status === 'trained',
  ).length
  const badge = assignment.status ? assignmentStatusBadge(assignment.status) : null
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Turmas', href: '/classrooms' },
          { label: classroom.name, href: classroomPath(classroom.id) },
          { label: assignment.name },
          { label: 'Conceitos' },
        ]}
      />
      <PageHeader
        title="Conceitos"
        badge={
          badge ? (
            <Badge tone={badge.tone} icon={badge.icon}>
              {badge.label}
            </Badge>
          ) : null
        }
        description={DESCRIPTION}
      />
      <AssignmentWorkspace key={assignment.id} assignment={assignment} />
      {assignment.status && isEditable(assignment.status) ? (
        <ApprovalBar
          assignmentId={assignment.id}
          status={assignment.status}
          approvedCount={approvedCount}
          assignmentCount={assignments.length}
        />
      ) : null}
    </>
  )
}
