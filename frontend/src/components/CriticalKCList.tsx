// Critical-KC list (DASH-02). The backend authors critical_kcs weakest-first; this component maps it in
// array order and MUST NOT sort — re-ranking client-side would diverge from the source of truth (D-08).

import type { CriticalKC } from '../api/schema'
import { formatPercent } from '../lib/format'

const MONO = 'ui-monospace, "SF Mono", "Cascadia Code", monospace'

export function CriticalKCList({ criticalKcs }: { criticalKcs: CriticalKC[] }) {
  return (
    <section>
      <h3>KCs críticos da turma</h3>
      <ul>
        {criticalKcs.map((kc) => (
          <li key={kc.kc_id}>
            <span style={{ fontFamily: MONO }}>{kc.kc_id}</span>{' '}
            <span style={{ fontFamily: MONO }}>{formatPercent(kc.mean_mastery)}</span>
          </li>
        ))}
      </ul>
    </section>
  )
}
