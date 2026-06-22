// Reinforcement recommendations (REC-01). The backend pre-renders each suggestion's pt-BR `text`
// (recommendations.py:35) and ranks them weakest-first; the SPA shows `text` VERBATIM as JSX (React
// auto-escapes — never dangerouslySetInnerHTML, T-06.1-09) and keeps the backend array order (no
// client re-sort, D-08). An empty array means no model is trained → the recs-untrained empty-state.

import type { Recommendation } from '../api/schema'
import { EmptyState } from './states/EmptyState'

export function RecommendationList({
  recommendations,
}: {
  recommendations: Recommendation[]
}) {
  if (recommendations.length === 0) {
    return (
      <section>
        <h3 className="t-heading">Recomendações de reforço</h3>
        <EmptyState kind="recs-untrained" />
      </section>
    )
  }

  return (
    <section>
      <h3 className="t-heading">Recomendações de reforço</h3>
      <ul className="rec-list">
        {recommendations.map((rec) => (
          // text shown verbatim; never reconstructed from kc_name/guidance/mean_mastery client-side.
          <li key={rec.kc_id} className="rec-list__item">
            {rec.text}
          </li>
        ))}
      </ul>
    </section>
  )
}
