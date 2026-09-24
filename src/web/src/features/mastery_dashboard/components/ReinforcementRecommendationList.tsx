import type { ReinforcementRecommendation } from '../api/useReinforcementRecommendations'
import { DashboardEmptyState } from './DashboardEmptyState'

// O texto vem pronto do backend, em pt-BR, e aparece como veio e na ordem que veio
export function ReinforcementRecommendationList({
  recommendations,
}: {
  recommendations: ReinforcementRecommendation[]
}) {
  return (
    <section>
      <h3 className="t-section-title">Recomendações de reforço</h3>
      {recommendations.length === 0 ? (
        <DashboardEmptyState kind="recommendations-untrained" />
      ) : (
        <ul className="rec-list">
          {recommendations.map((recommendation) => (
            <li key={recommendation.kc_id} className="rec-list__item">
              {recommendation.text}
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
