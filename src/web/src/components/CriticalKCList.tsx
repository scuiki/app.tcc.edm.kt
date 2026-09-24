// Critical-KC list (DASH-02). The backend authors critical_kcs weakest-first; this component maps it in
// array order and MUST NOT sort — re-ranking client-side would diverge from the source of truth (D-08).

import type { CriticalKC } from '../http/schema'
import { formatPercent } from '../lib/format'

export function CriticalKCList({ criticalKcs }: { criticalKcs: CriticalKC[] }) {
  return (
    <section>
      <h3 className="t-heading">KCs críticos da turma</h3>
      <ul className="data-list">
        {criticalKcs.map((kc) => (
          <li key={kc.kc_id} className="data-list__row">
            <span className="data-list__label mono">{kc.kc_id}</span>
            <span className="data-list__value mono">{formatPercent(kc.mean_mastery)}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
