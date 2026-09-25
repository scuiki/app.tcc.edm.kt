import { useState } from 'react'
import { Users } from 'lucide-react'

import { PageHeader } from '../../../components/PageHeader'
import { EmptyState, QueryStates } from '../../../components/states/states'
import { Card } from '../../../components/ui/Card'
import { hashParam } from '../../../lib/hashRoute'
import { useAssignments } from '../../assignments/api/useAssignments'
import { useClassrooms, type ClassroomSummary } from '../../classrooms/api/classrooms'
import { ApprovalBar } from '../components/ApprovalBar'
import { AssignmentPicker } from '../components/AssignmentPicker'
import { AssignmentWorkspace } from '../components/AssignmentWorkspace'
import { isEditable } from '../knowledgeComponents'
import './KnowledgeComponentsPage.css'

const DESCRIPTION =
  'O modelo sugere os conceitos a partir das soluções corretas. Ajuste o que não bater com a sua disciplina e aprove para liberar o treino.'

export function KnowledgeComponentsPage() {
  const query = useClassrooms()
  const classrooms = query.data?.classrooms ?? []
  if (classrooms.length > 0) return <KnowledgeComponentsBoard classrooms={classrooms} />
  return (
    <>
      <PageHeader title="Conceitos" description={DESCRIPTION} />
      <Card title="Exercícios">
        <QueryStates
          query={query}
          loadingLabel="Carregando turmas…"
          isEmpty={(data) => data.classrooms.length === 0}
          empty={
            <EmptyState
              icon={Users}
              title="Nenhuma turma ainda"
              text="Os conceitos são extraídos dos exercícios de uma turma. Crie a turma e importe os dados dela primeiro."
              action={<a href="#/classrooms">Ir para Turmas</a>}
            />
          }
        >
          {() => null}
        </QueryStates>
      </Card>
    </>
  )
}

// A turma pode vir no hash, como quando o professor chega da importação
function initialClassroomId(classrooms: ClassroomSummary[]): number | null {
  const fromHash = Number(hashParam(window.location.hash, 'classroom'))
  if (classrooms.some((classroom) => classroom.id === fromHash)) return fromHash
  return classrooms.length === 1 ? classrooms[0].id : null
}

function KnowledgeComponentsBoard({ classrooms }: { classrooms: ClassroomSummary[] }) {
  const [classroomId, setClassroomId] = useState(() => initialClassroomId(classrooms))
  const [assignmentId, setAssignmentId] = useState<number | null>(null)
  const assignmentsQuery = useAssignments(classroomId)
  const assignments = classroomId == null ? [] : (assignmentsQuery.data?.assignments ?? [])
  const assignment = assignments.find((candidate) => candidate.id === assignmentId)
  const approvedCount = assignments.filter(
    (candidate) => candidate.status === 'kc_approved' || candidate.status === 'trained',
  ).length

  function handleClassroomChange(id: number) {
    setClassroomId(id)
    setAssignmentId(null)
  }

  return (
    <>
      <PageHeader title="Conceitos" description={DESCRIPTION} />
      <div className="kc-page">
        <div className="kc-page__picker">
          <AssignmentPicker
            classrooms={classrooms}
            classroomId={classroomId}
            onClassroomChange={handleClassroomChange}
            assignmentsQuery={assignmentsQuery}
            assignmentId={assignmentId}
            onAssignmentChange={setAssignmentId}
          />
        </div>
        <div className="kc-page__main">
          {assignment ? (
            <AssignmentWorkspace key={assignment.id} assignment={assignment} />
          ) : (
            <Card title="Conceitos por problema">
              <EmptyState
                title="Escolha um exercício"
                text="Os conceitos de cada exercício aparecem aqui, problema por problema."
              />
            </Card>
          )}
        </div>
      </div>
      {assignment?.status && isEditable(assignment.status) ? (
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
