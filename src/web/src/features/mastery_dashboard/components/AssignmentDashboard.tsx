import type { AssignmentSummary } from '../../assignments/api/useAssignments'
import { dashboardStateOf } from '../dashboard'
import { AnalysisCard } from './AnalysisCard'
import { NoApprovedConceptsCard, NotTrainableCard, TrainModelCard } from './AssignmentStateCards'
import './AssignmentDashboard.css'

interface AssignmentDashboardProps {
  assignment: AssignmentSummary
  classroomId: number
  onTrain: () => void
}

// O conteúdo do exercício; a situação dele decide o cartão de cima e as colunas do modelo
export function AssignmentDashboard({
  assignment,
  classroomId,
  onTrain,
}: AssignmentDashboardProps) {
  const state = dashboardStateOf(assignment.status)
  return (
    <div className="assignment-dashboard">
      {state === 'not_trainable' ? <NotTrainableCard /> : null}
      {state === 'no_approved_concepts' ? (
        <NoApprovedConceptsCard classroomId={classroomId} assignmentId={assignment.id} />
      ) : null}
      {state === 'ready_to_train' ? <TrainModelCard onTrain={onTrain} /> : null}
      <AnalysisCard assignmentId={assignment.id} state={state} />
    </div>
  )
}
