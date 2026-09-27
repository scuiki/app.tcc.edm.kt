import type { AssignmentSummary } from '../../assignments/api/useAssignments'
import { dashboardStateOf } from '../dashboard'
import { useTraining } from '../useTraining'
import { AnalysisCard } from './AnalysisCard'
import { NoApprovedConceptsCard, NotTrainableCard, TrainModelCard } from './AssignmentStateCards'
import { TrainingDialog } from './TrainingDialog'
import './AssignmentDashboard.css'

interface AssignmentDashboardProps {
  assignment: AssignmentSummary
  classroomId: number
}

// O conteúdo do exercício; a situação dele decide o cartão de cima e as colunas do modelo
export function AssignmentDashboard({ assignment, classroomId }: AssignmentDashboardProps) {
  const state = dashboardStateOf(assignment.status)
  const training = useTraining(assignment.id)
  return (
    <div className="assignment-dashboard">
      {state === 'not_trainable' ? <NotTrainableCard /> : null}
      {state === 'no_approved_concepts' ? (
        <NoApprovedConceptsCard classroomId={classroomId} assignmentId={assignment.id} />
      ) : null}
      {state === 'ready_to_train' ? <TrainModelCard onTrain={training.begin} /> : null}
      <AnalysisCard assignmentId={assignment.id} state={state} />
      <TrainingDialog training={training} assignmentName={assignment.name} />
    </div>
  )
}
