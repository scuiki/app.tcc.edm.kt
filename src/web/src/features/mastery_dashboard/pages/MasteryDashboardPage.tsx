import { useState } from 'react'

import { PageHeader } from '../../../components/PageHeader'
import { QueryStates } from '../../../components/states/states'
import { useAssignments, type AssignmentSummary } from '../../assignments/api/useAssignments'
import { useMastery } from '../api/useMastery'
import { usePreTrainingStatistics } from '../api/usePreTrainingStatistics'
import { useReinforcementRecommendations } from '../api/useReinforcementRecommendations'
import { CriticalKnowledgeComponentList } from '../components/CriticalKnowledgeComponentList'
import { DashboardEmptyState } from '../components/DashboardEmptyState'
import { PreTrainingStatisticsCharts } from '../components/PreTrainingStatisticsCharts'
import { ReinforcementRecommendationList } from '../components/ReinforcementRecommendationList'
import { StudentMasteryHeatmap } from '../components/StudentMasteryHeatmap'
import { StudentsAtRiskList } from '../components/StudentsAtRiskList'
import { TrainedModelInfoNote } from '../components/TrainedModelInfoNote'
import './MasteryDashboardPage.css'

type Tab = 'mastery' | 'pre-training-statistics' | 'recommendations'

const TABS: { id: Tab; label: string }[] = [
  { id: 'mastery', label: 'Domínio (mastery)' },
  { id: 'pre-training-statistics', label: 'Análise exploratória' },
  { id: 'recommendations', label: 'Recomendações de reforço' },
]

const LOADING_LABEL = 'Carregando dados da turma…'
const ERROR_MESSAGE =
  'Não foi possível carregar os dados do dashboard. Verifique se a API está no ar e tente novamente.'

export function MasteryDashboardPage() {
  const [assignmentId, setAssignmentId] = useState<number | null>(null)
  const [tab, setTab] = useState<Tab>('mastery')
  const assignmentsQuery = useAssignments()

  return (
    <>
      <PageHeader title="Domínio da turma" />
      <div className="dashboard">
        <nav aria-label="Turma / Assignment" className="dashboard-rail">
          <p className="dashboard-rail__label">Turma / Assignment</p>
          <QueryStates
            query={assignmentsQuery}
            loadingLabel={LOADING_LABEL}
            errorMessage={ERROR_MESSAGE}
            isEmpty={(data) => data.assignments.length === 0}
            empty={<DashboardEmptyState kind="no-assignments" />}
          >
            {(data) => (
              <AssignmentList
                assignments={data.assignments}
                selectedId={assignmentId}
                onSelect={setAssignmentId}
              />
            )}
          </QueryStates>
        </nav>
        <div className="dashboard__main">
          <TabList active={tab} onChange={setTab} />
          <section className="dashboard__content">
            {assignmentId == null ? (
              // A lista vazia já avisa na coluna, então aqui só se pede a escolha
              assignmentsQuery.data?.assignments.length ? (
                <DashboardEmptyState kind="select-assignment" />
              ) : null
            ) : (
              <TabContent tab={tab} assignmentId={assignmentId} />
            )}
          </section>
        </div>
      </div>
    </>
  )
}

interface AssignmentListProps {
  assignments: AssignmentSummary[]
  selectedId: number | null
  onSelect: (id: number) => void
}

function AssignmentList({ assignments, selectedId, onSelect }: AssignmentListProps) {
  return (
    <ul className="dashboard-rail__list">
      {assignments.map((assignment) => (
        <li key={assignment.id}>
          <button
            type="button"
            className="dashboard-rail__item"
            aria-current={assignment.id === selectedId ? 'true' : undefined}
            onClick={() => onSelect(assignment.id)}
          >
            {assignment.name}
          </button>
        </li>
      ))}
    </ul>
  )
}

function TabList({ active, onChange }: { active: Tab; onChange: (tab: Tab) => void }) {
  return (
    <div role="tablist" className="tabs">
      {TABS.map((tab) => (
        <button
          key={tab.id}
          type="button"
          role="tab"
          className="tabs__tab"
          aria-selected={tab.id === active}
          onClick={() => onChange(tab.id)}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

function TabContent({ tab, assignmentId }: { tab: Tab; assignmentId: number }) {
  if (tab === 'mastery') return <MasteryTab assignmentId={assignmentId} />
  if (tab === 'pre-training-statistics') {
    return <PreTrainingStatisticsTab assignmentId={assignmentId} />
  }
  return <RecommendationsTab assignmentId={assignmentId} />
}

function MasteryTab({ assignmentId }: { assignmentId: number }) {
  const query = useMastery(assignmentId)
  return (
    <QueryStates query={query} loadingLabel={LOADING_LABEL} errorMessage={ERROR_MESSAGE}>
      {(data) => (
        <div className="stack stack--wide">
          <TrainedModelInfoNote
            firstAttemptAuc={data.first_attempt_auc}
            trainedAt={data.trained_at}
          />
          <div className="panel">
            <StudentMasteryHeatmap matrix={data.matrix} firstAttemptAuc={data.first_attempt_auc} />
          </div>
          <CriticalKnowledgeComponentList kcs={data.critical_kcs} />
          <StudentsAtRiskList studentIds={data.students_at_risk} />
        </div>
      )}
    </QueryStates>
  )
}

function PreTrainingStatisticsTab({ assignmentId }: { assignmentId: number }) {
  const query = usePreTrainingStatistics(assignmentId)
  return (
    <QueryStates query={query} loadingLabel={LOADING_LABEL} errorMessage={ERROR_MESSAGE}>
      {(data) => <PreTrainingStatisticsCharts statistics={data} />}
    </QueryStates>
  )
}

function RecommendationsTab({ assignmentId }: { assignmentId: number }) {
  const query = useReinforcementRecommendations(assignmentId)
  return (
    <QueryStates query={query} loadingLabel={LOADING_LABEL} errorMessage={ERROR_MESSAGE}>
      {(data) => <ReinforcementRecommendationList recommendations={data.recommendations} />}
    </QueryStates>
  )
}
