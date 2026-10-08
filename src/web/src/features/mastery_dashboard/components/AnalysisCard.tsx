import { useState } from 'react'
import { Blocks, FileCode, Users } from 'lucide-react'

import { GeneratedByML } from '../../../components/GeneratedByML'
import { EmptyState, QueryStates } from '../../../components/states/states'
import { Card } from '../../../components/ui/Card'
import { Tabs, type TabItem } from '../../../components/ui/Tabs'
import { useMastery, useStudents, useSubmissionStatistics } from '../api/masteryDashboard'
import {
  hasApprovedConcepts,
  mergeConcepts,
  mergeProblems,
  type AnalysisTab,
  type DashboardState,
} from '../dashboard'
import { ConceptsTable } from './ConceptsTable'
import { ProblemsTable } from './ProblemsTable'
import { StudentDialog } from './StudentDialog'
import { StudentsTable } from './StudentsTable'
import './AnalysisTable.css'

const TABS: TabItem<AnalysisTab>[] = [
  { key: 'problems', label: 'Problemas', icon: FileCode },
  { key: 'concepts', label: 'Conceitos', icon: Blocks },
  { key: 'students', label: 'Alunos', icon: Users },
]

interface AnalysisCardProps {
  assignmentId: number
  state: DashboardState
}

// O cartão da Análise, uma tabela por aba, o que aconteceu e o que o modelo estima lado a lado
export function AnalysisCard({ assignmentId, state }: AnalysisCardProps) {
  const [tab, setTab] = useState<AnalysisTab>('problems')
  const [studentId, setStudentId] = useState<string | null>(null)
  const withModel = state === 'trained'
  const statistics = useSubmissionStatistics(assignmentId)
  const mastery = useMastery(assignmentId)
  const problemCount = statistics.data?.problems.length ?? 0

  // A nota só faz sentido quando há colunas com o marcador, ou seja, com modelo treinado
  const note = withModel ? (
    <p className="analysis-note">
      O marcador <GeneratedByML /> representa dados estimados pelo modelo de aprendizado de máquina.
    </p>
  ) : null
  return (
    <Card footer={note}>
      <Tabs items={TABS} active={tab} onChange={setTab} label="O que analisar" />
      <QueryStates query={statistics} loadingLabel="Contando as execuções…">
        {(data) => {
          if (tab === 'problems') {
            return data.problems.length === 0 ? (
              <div className="analysis-empty">
                <EmptyState text="Este exercício ainda não tem execuções importadas." />
              </div>
            ) : (
              <ProblemsTable
                problems={mergeProblems(data.problems, mastery.data?.problems ?? [])}
                withModel={withModel}
              />
            )
          }
          if (tab === 'concepts') {
            return !hasApprovedConcepts(state) ? (
              <div className="analysis-empty">
                <EmptyState text="Os conceitos entram aqui depois de aprovados em Conceitos." />
              </div>
            ) : (
              <ConceptsTable
                concepts={mergeConcepts(
                  data.knowledge_components,
                  mastery.data?.knowledge_components ?? [],
                )}
                withModel={withModel}
              />
            )
          }
          return withModel ? (
            <StudentsTab
              assignmentId={assignmentId}
              problemCount={problemCount}
              onOpen={setStudentId}
            />
          ) : (
            <div className="analysis-empty">
              <EmptyState text="Os alunos entram aqui depois de treinar o modelo." />
            </div>
          )
        }}
      </QueryStates>
      <StudentDialog
        assignmentId={assignmentId}
        problemCount={problemCount}
        studentId={studentId}
        onClose={() => setStudentId(null)}
      />
    </Card>
  )
}

function StudentsTab({
  assignmentId,
  problemCount,
  onOpen,
}: {
  assignmentId: number
  problemCount: number
  onOpen: (studentId: string) => void
}) {
  const query = useStudents(assignmentId)
  return (
    <QueryStates query={query} loadingLabel="Carregando os alunos…">
      {(data) => (
        <StudentsTable students={data.students} problemCount={problemCount} onOpen={onOpen} />
      )}
    </QueryStates>
  )
}
