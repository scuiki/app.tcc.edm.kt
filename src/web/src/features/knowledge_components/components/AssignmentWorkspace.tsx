import { Sparkles } from 'lucide-react'

import { FactsLine, type Fact } from '../../../components/FactsLine'
import { PageHeader } from '../../../components/PageHeader'
import { EmptyState, QueryStates } from '../../../components/states/states'
import { Badge } from '../../../components/ui/Badge'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { formatCount, formatDate } from '../../../lib/format'
import { assignmentStatusBadge, type AssignmentSummary } from '../../assignments/api/useAssignments'
import { useAssignmentProblems } from '../api/knowledgeComponents'
import {
  factsLineCountsOf,
  hasKnowledgeComponents,
  type FactsLineCounts,
} from '../knowledgeComponents'
import { useExtraction } from '../useExtraction'
import { ExtractionDialog } from './ExtractionDialog'
import { KnowledgeComponentEditor } from './KnowledgeComponentEditor'

function counted(count: number, singular: string, plural: string) {
  return (
    <>
      <span className="num">{formatCount(count)}</span> {count === 1 ? singular : plural}
    </>
  )
}

// Sem conceitos a linha traz só os problemas, e a data some quando não há extração concluída
function factsOf(counts: FactsLineCounts, extractedAt: string | null): Fact[] {
  const facts: Fact[] = [{ content: counted(counts.problemCount, 'problema', 'problemas') }]
  if (counts.knowledgeComponentCount === 0) return facts
  facts.push({ content: counted(counts.knowledgeComponentCount, 'conceito', 'conceitos') })
  if (extractedAt) {
    facts.push({
      content: (
        <>
          {counts.knowledgeComponentCount === 1 ? 'extraído em' : 'extraídos em'}{' '}
          <span className="num">{formatDate(extractedAt)}</span>
        </>
      ),
    })
  }
  const withoutKnowledgeComponent = counts.problemsWithoutKnowledgeComponent.length
  facts.push(
    withoutKnowledgeComponent > 0
      ? {
          content: counted(
            withoutKnowledgeComponent,
            'problema sem conceito',
            'problemas sem conceito',
          ),
          alert: true,
        }
      : { content: 'nenhum problema sem conceito' },
  )
  return facts
}

// Fica montado quando a situação muda, para o diálogo da extração mostrar o desfecho
export function AssignmentWorkspace({ assignment }: { assignment: AssignmentSummary }) {
  const query = useAssignmentProblems(assignment.id)
  const extraction = useExtraction(assignment.id)
  const counts = factsLineCountsOf(query.data?.problems ?? [])
  const result =
    counts.knowledgeComponentCount > 0
      ? {
          knowledgeComponents: counts.knowledgeComponentCount,
          problemsCovered: counts.problemCount - counts.problemsWithoutKnowledgeComponent.length,
        }
      : null
  const badge = assignment.status ? assignmentStatusBadge(assignment.status) : null

  // O cabeçalho fica fora do QueryStates, para o título e a etiqueta aparecerem junto do caminho
  return (
    <>
      <PageHeader
        title={assignment.name}
        badge={
          badge ? (
            <Badge tone={badge.tone} icon={badge.icon}>
              {badge.label}
            </Badge>
          ) : null
        }
        facts={query.data ? <FactsLine facts={factsOf(counts, query.data.extracted_at)} /> : null}
      />
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
