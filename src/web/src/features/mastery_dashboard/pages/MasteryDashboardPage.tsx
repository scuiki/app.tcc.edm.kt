import { ChartColumn } from 'lucide-react'

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
import { AssignmentDashboard } from '../components/AssignmentDashboard'

const DESCRIPTION =
  'O que aconteceu nas execuções e o que o modelo prevê, por problema, conceito e aluno.'

interface MasteryDashboardPageProps {
  classroomId?: number
  assignmentId?: number
}

// O exercício vem do endereço; a página é a análise dele
export function MasteryDashboardPage({ classroomId, assignmentId }: MasteryDashboardPageProps) {
  const context = useAssignmentContext(classroomId, assignmentId)
  if (context.isPending) return <LoadingState label="Carregando o exercício…" />
  if (context.isError) return <ErrorState />
  const { classroom, assignment } = context
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
  const badge = assignment.status ? assignmentStatusBadge(assignment.status) : null
  return (
    <>
      <Breadcrumb
        items={[
          { label: 'Turmas', href: '/classrooms' },
          { label: classroom.name, href: classroomPath(classroom.id) },
          { label: assignment.name },
          { label: 'Análise' },
        ]}
        aside={
          badge ? (
            <Badge tone={badge.tone} icon={badge.icon}>
              {badge.label}
            </Badge>
          ) : null
        }
      />
      <PageHeader title={assignment.name} icon={ChartColumn} description={DESCRIPTION} />
      <AssignmentDashboard key={assignment.id} assignment={assignment} classroomId={classroom.id} />
    </>
  )
}
