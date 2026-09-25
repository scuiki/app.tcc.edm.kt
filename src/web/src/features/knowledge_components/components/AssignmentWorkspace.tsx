import { Sparkles } from 'lucide-react'

import { EmptyState, QueryStates } from '../../../components/states/states'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import type { AssignmentSummary } from '../../assignments/api/useAssignments'
import { useAssignmentProblems } from '../api/knowledgeComponents'
import { hasKnowledgeComponents, knowledgeComponentsOf } from '../knowledgeComponents'
import { useExtraction } from '../useExtraction'
import { ExtractionDialog } from './ExtractionDialog'
import { KnowledgeComponentEditor } from './KnowledgeComponentEditor'

// Fica montado quando a situação muda, para o diálogo da extração mostrar o desfecho
export function AssignmentWorkspace({ assignment }: { assignment: AssignmentSummary }) {
  const query = useAssignmentProblems(assignment.id)
  const extraction = useExtraction(assignment.id)
  const problems = query.data?.problems ?? []
  const knowledgeComponents = knowledgeComponentsOf(problems)
  const result =
    knowledgeComponents.length > 0
      ? {
          knowledgeComponents: knowledgeComponents.length,
          problemsCovered: problems.filter((problem) => problem.knowledge_components.length > 0)
            .length,
        }
      : null

  return (
    <>
      <QueryStates query={query} loadingLabel="Carregando os conceitos do exercício…">
        {(data) =>
          hasKnowledgeComponents(data.status) ? (
            <KnowledgeComponentEditor
              assignmentId={assignment.id}
              status={data.status}
              problems={data.problems}
            />
          ) : (
            <Card title="Conceitos por problema">
              {data.status === 'ready_for_kc_generation' ? (
                <EmptyState
                  icon={Sparkles}
                  title="Sem conceitos ainda"
                  text="O modelo lê as soluções corretas de cada problema e sugere os conceitos que ele exige. Leva alguns minutos, e você revisa tudo antes de aprovar."
                  action={
                    <Button variant="primary" onClick={extraction.begin}>
                      Extrair conceitos
                    </Button>
                  }
                />
              ) : (
                <EmptyState
                  title="Não há conceitos para extrair"
                  text="Este exercício não tem acertos e erros suficientes para treinar, e só as estatísticas ficam disponíveis."
                />
              )}
            </Card>
          )
        }
      </QueryStates>
      <ExtractionDialog extraction={extraction} assignmentName={assignment.name} result={result} />
    </>
  )
}
