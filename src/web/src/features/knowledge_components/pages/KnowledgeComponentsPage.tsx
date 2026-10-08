import { Breadcrumb } from '../../../components/Breadcrumb'
import { EmptyState, ErrorState, LoadingState } from '../../../components/states/states'
import { Card } from '../../../components/ui/Card'
import { classroomPath } from '../../../lib/paths'
import { useAssignmentContext } from '../../assignments/api/useAssignmentContext'
import { AssignmentWorkspace } from '../components/AssignmentWorkspace'

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
  // O cabeçalho mora no AssignmentWorkspace, porque a linha de fatos lê a rota da tela
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
      <AssignmentWorkspace key={assignment.id} assignment={assignment} />
    </>
  )
}
