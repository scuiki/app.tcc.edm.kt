import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'

import type { PreTrainingStatistics, StatisticSeries } from '../api/usePreTrainingStatistics'
import { DashboardEmptyState } from './DashboardEmptyState'

// O Chart.js 4 só desenha as escalas e os elementos registrados
ChartJS.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Tooltip, Legend)

// O azul de ação, e nunca as cores das faixas de domínio
const SERIES_COLOR = '#0a5cff'

function pointsOf(series: StatisticSeries) {
  return { labels: Object.keys(series), data: Object.values(series) }
}

function isEmpty(series: StatisticSeries) {
  return Object.keys(series).length === 0
}

// Uma série vazia vira o estado vazio, porque um gráfico em branco parece zero erros
function SeriesChart({
  series,
  kind,
  label,
}: {
  series: StatisticSeries
  kind: 'bar' | 'line'
  label: string
}) {
  if (isEmpty(series)) return <DashboardEmptyState kind="pre-training-statistics" />
  const { labels, data } = pointsOf(series)
  return kind === 'bar' ? (
    <Bar data={{ labels, datasets: [{ label, data, backgroundColor: SERIES_COLOR }] }} />
  ) : (
    <Line data={{ labels, datasets: [{ label, data, borderColor: SERIES_COLOR }] }} />
  )
}

export function PreTrainingStatisticsCharts({ statistics }: { statistics: PreTrainingStatistics }) {
  return (
    <section className="stack">
      <h3 className="t-section-title">Análise exploratória (EDA)</h3>
      <div className="panel">
        <SeriesChart series={statistics.success_rate} kind="bar" label="Taxa de acerto" />
      </div>
      <div className="panel">
        <SeriesChart series={statistics.learning_curve} kind="line" label="Curva de aprendizado" />
      </div>
      <div className="panel">
        <SeriesChart
          series={statistics.compile_error_rate}
          kind="bar"
          label="Taxa de erro de compilação"
        />
      </div>
    </section>
  )
}
