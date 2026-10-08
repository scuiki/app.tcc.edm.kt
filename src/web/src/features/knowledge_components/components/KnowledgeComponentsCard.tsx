import { Merge, Pencil, Trash2 } from 'lucide-react'

import { IconButton } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import type { KnowledgeComponentUsage } from '../knowledgeComponents'
import './KnowledgeComponentsCard.css'

interface KnowledgeComponentsCardProps {
  knowledgeComponents: KnowledgeComponentUsage[]
  problemTotal: number
  problemsWithoutKnowledgeComponent: number
  // Sem as ações, o cartão fica só para consulta
  onRename?: (kcId: number) => void
  onMerge?: (kcId: number) => void
  onRemove?: (kcId: number) => void
  isBusy?: boolean
}

export function KnowledgeComponentsCard({
  knowledgeComponents,
  problemTotal,
  problemsWithoutKnowledgeComponent,
  onRename,
  onMerge,
  onRemove,
  isBusy,
}: KnowledgeComponentsCardProps) {
  return (
    <Card title="Conceitos do exercício">
      <div className="kc-summary">
        <div>
          <div className="kc-summary__value num">{knowledgeComponents.length}</div>
          <div className="kc-summary__label">conceitos</div>
        </div>
        <div>
          <div className="kc-summary__value num">{problemTotal}</div>
          <div className="kc-summary__label">problemas</div>
        </div>
      </div>
      <p
        className={`kc-summary__coverage${problemsWithoutKnowledgeComponent > 0 ? ' kc-summary__coverage--missing' : ''}`}
      >
        {coverageText(problemsWithoutKnowledgeComponent)}
      </p>
      <ul className="kc-usage">
        {knowledgeComponents.map((kc) => (
          <li key={kc.id} className="kc-usage__item">
            <div className="kc-usage__text">
              <span className="kc-usage__name">{kc.name}</span>
              <span className="t-support">
                marca {kc.problemIds.length} de {problemTotal}{' '}
                {problemTotal === 1 ? 'problema' : 'problemas'}
              </span>
            </div>
            {onRename && onMerge && onRemove ? (
              <div className="kc-usage__actions">
                <IconButton
                  icon={Pencil}
                  label={`Editar o nome de ${kc.name}`}
                  disabled={isBusy}
                  onClick={() => onRename(kc.id)}
                />
                <IconButton
                  icon={Merge}
                  label={`Mesclar ${kc.name} com outro conceito`}
                  disabled={isBusy || knowledgeComponents.length < 2}
                  onClick={() => onMerge(kc.id)}
                />
                <IconButton
                  icon={Trash2}
                  label={`Remover ${kc.name} do exercício`}
                  disabled={isBusy}
                  onClick={() => onRemove(kc.id)}
                />
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </Card>
  )
}

function coverageText(missing: number) {
  if (missing === 0) return 'Nenhum problema está sem conceito.'
  return missing === 1
    ? '1 problema está sem conceito.'
    : `${missing} problemas estão sem conceito.`
}
