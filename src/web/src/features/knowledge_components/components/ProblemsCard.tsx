import { Plus, X } from 'lucide-react'

import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import type { KnowledgeComponent, ProblemKnowledgeComponents } from '../api/knowledgeComponents'
import './ProblemsCard.css'

interface ProblemsCardProps {
  problems: ProblemKnowledgeComponents[]
  // Sem as ações, o cartão fica só para consulta
  onUnlink?: (kc: KnowledgeComponent, problemId: number) => void
  onAdd?: (problemId: number) => void
  isBusy?: boolean
}

export function ProblemsCard({ problems, onUnlink, onAdd, isBusy }: ProblemsCardProps) {
  return (
    <Card title="Conceitos por problema">
      <ul className="problem-list">
        {problems.map((problem) => (
          <li key={problem.problem_id} className="problem-list__item">
            <div className="problem-list__header">
              <span className="problem-list__title">Problema {problem.problem_id}</span>
              {problem.statement ? (
                <span className="problem-list__statement">{problem.statement}</span>
              ) : null}
            </div>
            <div className="problem-list__chips">
              {problem.knowledge_components.map((kc) => (
                <span key={kc.id} className={`kc-chip${onUnlink ? '' : ' kc-chip--readonly'}`}>
                  {kc.name}
                  {onUnlink ? (
                    <button
                      type="button"
                      className="kc-chip__remove"
                      aria-label={`Tirar ${kc.name} do problema ${problem.problem_id}`}
                      title={`Tirar do problema ${problem.problem_id}`}
                      disabled={isBusy}
                      onClick={() => onUnlink(kc, problem.problem_id)}
                    >
                      <X size={13} strokeWidth={2.6} aria-hidden="true" />
                    </button>
                  ) : null}
                </span>
              ))}
              {problem.knowledge_components.length === 0 ? (
                <span className="problem-list__empty">Sem nenhum conceito</span>
              ) : null}
              {onAdd ? (
                <Button
                  variant="secondary"
                  size="compact"
                  icon={Plus}
                  disabled={isBusy}
                  onClick={() => onAdd(problem.problem_id)}
                  aria-label={`Adicionar conceito ao problema ${problem.problem_id}`}
                >
                  Adicionar
                </Button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </Card>
  )
}
