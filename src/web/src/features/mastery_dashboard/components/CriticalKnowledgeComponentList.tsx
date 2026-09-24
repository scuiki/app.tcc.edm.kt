import { formatPercent } from '../../../lib/format'
import type { CriticalKnowledgeComponent } from '../api/useMastery'

// A ordem é a do backend, do mais fraco ao mais forte, e a tela nunca reordena
export function CriticalKnowledgeComponentList({ kcs }: { kcs: CriticalKnowledgeComponent[] }) {
  return (
    <section>
      <h3 className="t-section-title">KCs críticos da turma</h3>
      <ul className="data-list">
        {kcs.map((kc) => (
          <li key={kc.kc_id} className="data-list__row">
            <span className="mono">{kc.kc_id}</span>
            <span className="data-list__value mono">{formatPercent(kc.mean_mastery)}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
