import { CircleAlert, Pencil, Trash2 } from 'lucide-react'

import { GeneratedByLLM } from '../../../components/GeneratedByLLM'
import { IconButton } from '../../../components/ui/Button'
import { ColumnHeader, ColumnLabel, DataTable } from '../../../components/ui/DataTable'
import { Tooltip } from '../../../components/ui/Tooltip'
import { formatCount } from '../../../lib/format'
import type { ProblemKnowledgeComponents } from '../api/knowledgeComponents'
import type { KnowledgeComponentUsage } from '../knowledgeComponents'
import './KnowledgeComponentMatrix.css'

// As larguras do colgroup, e a coluna do nome fica com a sobra do cartão
const NAME_MIN_WIDTH = 220
const PROBLEM_WIDTH = 48
const RECURRENCE_WIDTH = 96
const ACTIONS_WIDTH = 84

const NOBODY_SOLVED =
  'Ninguém acertou este problema ainda. O modelo de linguagem precisa de execuções corretas para extrair conceitos. Ligue um conceito clicando nas células.'
const WITHOUT_KNOWLEDGE_COMPONENT =
  'Este problema está sem conceito. Ligue um conceito clicando nas células.'

interface KnowledgeComponentMatrixProps {
  problems: ProblemKnowledgeComponents[]
  // Os conceitos já na ordem das linhas, que o editor mantém fixa
  knowledgeComponents: KnowledgeComponentUsage[]
  // Sem as ações, a matriz fica só para consulta, como no exercício treinado
  onCellClick?: (kcId: number, problemId: number) => void
  onRename?: (kcId: number) => void
  onRemove?: (kcId: number) => void
}

// Os conceitos nas linhas e os problemas nas colunas, com uma célula por vínculo
export function KnowledgeComponentMatrix({
  problems,
  knowledgeComponents,
  onCellClick,
  onRename,
  onRemove,
}: KnowledgeComponentMatrixProps) {
  const hasActions = onRename != null && onRemove != null
  const minWidth =
    NAME_MIN_WIDTH +
    PROBLEM_WIDTH * problems.length +
    RECURRENCE_WIDTH +
    (hasActions ? ACTIONS_WIDTH : 0)
  return (
    <DataTable label="Conceitos por problema" minWidth={minWidth} fixedLayout stickyFirstColumn>
      <colgroup>
        <col />
        {problems.map((problem) => (
          <col key={problem.problem_id} style={{ width: PROBLEM_WIDTH }} />
        ))}
        <col style={{ width: RECURRENCE_WIDTH }} />
        {hasActions ? <col style={{ width: ACTIONS_WIDTH }} /> : null}
      </colgroup>
      <thead>
        <tr>
          <ColumnHeader label="Conceito" />
          {problems.map((problem) => (
            <th key={problem.problem_id} scope="col">
              <ProblemNumber problem={problem} />
            </th>
          ))}
          <ColumnHeader label="Recorrência" />
          {hasActions ? (
            <th scope="col" className="data-table__actions">
              <span className="visually-hidden">Ações</span>
            </th>
          ) : null}
        </tr>
      </thead>
      <tbody>
        {knowledgeComponents.map((kc) => (
          <tr key={kc.id}>
            <td>
              <span className="kc-matrix__name">
                <ColumnLabel text={kc.name} fillCell />
                {kc.is_generated_by_llm ? <GeneratedByLLM /> : null}
              </span>
            </td>
            {problems.map((problem) => (
              <td key={problem.problem_id} className="kc-matrix__link">
                <button
                  type="button"
                  className="kc-matrix__toggle"
                  aria-pressed={kc.problemIds.includes(problem.problem_id)}
                  aria-label={`${kc.name} no problema ${problem.problem_id}`}
                  disabled={!onCellClick}
                  onClick={() => onCellClick?.(kc.id, problem.problem_id)}
                />
              </td>
            ))}
            <td className="data-table__num">
              {formatCount(kc.problemIds.length)}{' '}
              <span className="data-table__sub">de {formatCount(problems.length)}</span>
            </td>
            {hasActions ? (
              <td className="data-table__actions">
                <IconButton
                  icon={Pencil}
                  label={`Editar o nome de ${kc.name}`}
                  onClick={() => onRename(kc.id)}
                />
                <IconButton
                  icon={Trash2}
                  label={`Remover ${kc.name} do exercício`}
                  onClick={() => onRemove(kc.id)}
                />
              </td>
            ) : null}
          </tr>
        ))}
      </tbody>
      <tfoot>
        <tr className="kc-matrix__totals">
          <td>Conceitos por problema</td>
          {problems.map((problem) => (
            <td key={problem.problem_id} className="data-table__num">
              {problem.knowledge_components.length === 0 ? (
                <span className="kc-matrix__zero">
                  <CircleAlert size={13} aria-hidden="true" />0
                </span>
              ) : (
                formatCount(problem.knowledge_components.length)
              )}
            </td>
          ))}
          <td />
          {hasActions ? <td /> : null}
        </tr>
      </tfoot>
    </DataTable>
  )
}

// O número leva o enunciado no balão, e o do problema sem conceito diz antes por que ele está vazio
function ProblemNumber({ problem }: { problem: ProblemKnowledgeComponents }) {
  const problemId = problem.problem_id
  if (problem.knowledge_components.length > 0) {
    return (
      <Tooltip
        size="wide"
        title={`Problema ${problemId}`}
        text={problem.statement ?? 'Sem enunciado.'}
      >
        <span className="kc-matrix__problem" tabIndex={0}>
          {problemId}
        </span>
      </Tooltip>
    )
  }
  const reason = problem.correct_run_count === 0 ? NOBODY_SOLVED : WITHOUT_KNOWLEDGE_COMPONENT
  return (
    <Tooltip
      size="wide"
      title={`Problema ${problemId} sem conceito`}
      text={problem.statement ? `${reason}\n\n${problem.statement}` : reason}
    >
      <span className="kc-matrix__problem kc-matrix__problem--empty" tabIndex={0}>
        <CircleAlert size={13} aria-hidden="true" />
        {problemId}
      </span>
    </Tooltip>
  )
}
