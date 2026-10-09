import { useState } from 'react'
import { FileCheck, FileCode } from 'lucide-react'

import { FactsLine } from '../../../components/FactsLine'
import { GeneratedByLLM } from '../../../components/GeneratedByLLM'
import { QueryStates } from '../../../components/states/states'
import { Button } from '../../../components/ui/Button'
import { CodeBlock } from '../../../components/ui/CodeBlock'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { InfoHint } from '../../../components/ui/InfoHint'
import { Tabs } from '../../../components/ui/Tabs'
import { formatCount } from '../../../lib/format'
import { useKnowledgeComponentOrigin, type ProblemOrigin } from '../api/knowledgeComponents'
import { problemOriginKindOf, type KnowledgeComponentUsage } from '../knowledgeComponents'
import './KnowledgeComponentOriginDialog.css'

const REASONING_HINT =
  'A frase em que o modelo de linguagem explica por que o problema exige o conceito, traduzida. Os números citados são os das abas das soluções.'
const SOLUTIONS_HINT =
  'As soluções corretas deste problema que o modelo de linguagem leu na extração, até cinco, na ordem em que as recebeu. As linhas destacadas mostram onde o modelo aponta o conceito, e não a causa da extração.'
const TEACHER_LINK =
  'O professor ligou este conceito a este problema. Não há justificativa nem trecho do modelo.'
const DISCARDED_EVIDENCE =
  'O modelo apontou um trecho que não está nas soluções, e o app o descartou.'
const NO_SOLUTIONS = 'Ninguém acertou este problema, então o modelo não leu nenhuma solução dele.'

interface KnowledgeComponentOriginDialogProps {
  knowledgeComponent?: KnowledgeComponentUsage
  // Os problemas do exercício, o total da linha de fatos
  problemCount: number
  onClose: () => void
}

// O título e a linha de fatos vêm da tela, e o resto chega pela rota da origem
export function KnowledgeComponentOriginDialog({
  knowledgeComponent,
  problemCount,
  onClose,
}: KnowledgeComponentOriginDialogProps) {
  return (
    <Dialog
      open={knowledgeComponent != null}
      onClose={onClose}
      size="wide"
      title={knowledgeComponent?.name ?? ''}
      titleAside={
        knowledgeComponent?.is_generated_by_llm ? <GeneratedByLLM variant="title" /> : null
      }
      facts={
        knowledgeComponent ? (
          <FactsLine
            facts={[
              {
                content: (
                  <>
                    aparece em{' '}
                    <span className="num">{formatCount(knowledgeComponent.problemIds.length)}</span>{' '}
                    de <span className="num">{formatCount(problemCount)}</span>{' '}
                    {problemCount === 1 ? 'problema' : 'problemas'}
                  </>
                ),
              },
            ]}
          />
        ) : null
      }
    >
      {knowledgeComponent ? <OriginOfKnowledgeComponent kcId={knowledgeComponent.id} /> : null}
      <DialogFooter>
        <Button variant="secondary" onClick={onClose}>
          Fechar
        </Button>
      </DialogFooter>
    </Dialog>
  )
}

function OriginOfKnowledgeComponent({ kcId }: { kcId: number }) {
  const origin = useKnowledgeComponentOrigin(kcId)
  return (
    <QueryStates
      query={origin}
      loadingLabel="Carregando a origem do conceito…"
      errorMessage="Não foi possível carregar a origem do conceito. Verifique se a API está no ar."
    >
      {(data) => <ProblemOrigins problems={data.problems} />}
    </QueryStates>
  )
}

// Uma aba por problema ligado, só com o número, porque o rótulo Problema vem uma vez antes delas
function ProblemOrigins({ problems }: { problems: ProblemOrigin[] }) {
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const problem = problems.find((item) => item.problem_id === selectedId) ?? problems[0]
  if (!problem) return null
  return (
    <>
      <div className="kc-origin__problems">
        <Tabs
          variant="identifier"
          items={problems.map((item) => ({
            key: String(item.problem_id),
            label: String(item.problem_id),
            ariaLabel: `Problema ${item.problem_id}`,
          }))}
          active={String(problem.problem_id)}
          onChange={(key) => setSelectedId(Number(key))}
          label="Problemas em que o conceito aparece"
          leading={
            <>
              <FileCode size={15} aria-hidden="true" />
              Problema
            </>
          }
        />
      </div>
      <DialogBody key={problem.problem_id}>
        <ProblemOriginPanel problem={problem} />
      </DialogBody>
    </>
  )
}

// O enunciado, a justificativa do modelo e as soluções que ele leu, nessa ordem
function ProblemOriginPanel({ problem }: { problem: ProblemOrigin }) {
  const kind = problemOriginKindOf(problem)
  const problemId = problem.problem_id
  return (
    <div className="kc-origin__panel" role="tabpanel" aria-label={`Problema ${problemId}`}>
      <section className="kc-origin__block">
        <h3 className="kc-origin__heading">
          Enunciado do problema{' '}
          <span className="num">{problemId}</span>
        </h3>
        {problem.statement ? (
          <p>{problem.statement}</p>
        ) : (
          <p className="kc-origin__no-statement">sem enunciado</p>
        )}
      </section>
      <section className="kc-origin__block">
        {kind === 'teacher_link' ? (
          <>
            <h3 className="kc-origin__heading">Justificativa do modelo de linguagem</h3>
            <p className="kc-origin__teacher-link">{TEACHER_LINK}</p>
          </>
        ) : (
          <>
            <div className="kc-origin__label">
              <GeneratedByLLM variant="label" />
              <h3 className="kc-origin__heading">Justificativa do modelo de linguagem</h3>
              <InfoHint text={REASONING_HINT} />
            </div>
            {problem.translated_reasonings.map((reasoning, index) => (
              <p key={index}>{reasoning}</p>
            ))}
          </>
        )}
      </section>
      <section className="kc-origin__block">
        <div className="kc-origin__label">
          <h3 className="kc-origin__heading">Soluções que o modelo leu</h3>
          <InfoHint text={SOLUTIONS_HINT} />
        </div>
        {problem.sampled_solutions.length === 0 ? (
          <p className="kc-origin__no-solutions">{NO_SOLUTIONS}</p>
        ) : (
          <>
            {kind === 'discarded_evidence' ? (
              <p className="kc-origin__discarded">{DISCARDED_EVIDENCE}</p>
            ) : null}
            <SampledSolutions problem={problem} />
          </>
        )}
      </section>
    </div>
  )
}

// O bloco abre na solução do trecho, com as linhas dele destacadas e as estrelas na aba
function SampledSolutions({ problem }: { problem: ProblemOrigin }) {
  const evidence = problem.evidence
  return (
    <CodeBlock
      label={`Soluções do problema ${problem.problem_id} que o modelo leu`}
      files={problem.sampled_solutions.map((solution) => {
        const hasEvidence = solution.position === evidence?.position
        return {
          key: solution.position,
          label: `Solução ${solution.position}`,
          code: solution.code,
          icon: FileCheck,
          marker: hasEvidence ? <GeneratedByLLM variant="tab" /> : undefined,
          ariaLabel: hasEvidence ? `Solução ${solution.position}, com o trecho` : undefined,
        }
      })}
      initialFile={evidence?.position}
      highlight={
        evidence
          ? {
              file: evidence.position,
              firstLine: evidence.first_line,
              lastLine: evidence.last_line,
            }
          : null
      }
    />
  )
}
