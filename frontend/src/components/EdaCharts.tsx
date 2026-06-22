// EDA charts (DASH-04). The three backend aggregates plot as success-rate (Bar), learning-curve
// (Line) and compile-error-rate (Bar). EDA reads only the canonical Parquet, so it is independent of
// training: the prop is just the EdaResponse payload — no first_auc, no model version. Each aggregate
// that arrives as {} degrades to the locked eda empty-state for that panel, never a blank canvas
// (Pitfall 2: a blank chart reads as "perfect / no errors"). The SPA only plots backend-authored
// values; it never recomputes an aggregate (D-08).

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

import type { EdaAggregate, EdaResponse } from '../api/schema'
import { EmptyState } from './states/EmptyState'

// Register once at module load — Chart.js 4 is tree-shaken, so the scales/elements each chart uses
// must be registered explicitly or rendering throws "not a registered scale".
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
)

// Brand palette only (06.1-FACENS-BRAND): the interactive accent blue for the primary series and the
// structural navy for the secondary. NOT the mastery band colors and NOT yellow — yellow is reserved
// for the mastery medium band, never chrome/decoration.
const SERIES_ACCENT = '#0a5cff'
const SERIES_NAVY = '#004479'

// int backend keys arrive as JSON string keys; labels = Object.keys, data = Object.values, in
// insertion order (the backend authored the ordering — no client re-sort).
function points(agg: EdaAggregate): { labels: string[]; data: number[] } {
  return { labels: Object.keys(agg), data: Object.values(agg) }
}

function isEmpty(agg: EdaAggregate): boolean {
  return Object.keys(agg).length === 0
}

function SuccessRatePanel({ agg }: { agg: EdaAggregate }) {
  if (isEmpty(agg)) return <EmptyState kind="eda" />
  const { labels, data } = points(agg)
  return (
    <Bar
      data={{ labels, datasets: [{ label: 'Taxa de acerto', data, backgroundColor: SERIES_ACCENT }] }}
    />
  )
}

function LearningCurvePanel({ agg }: { agg: EdaAggregate }) {
  if (isEmpty(agg)) return <EmptyState kind="eda" />
  const { labels, data } = points(agg)
  return (
    <Line
      data={{
        labels,
        datasets: [{ label: 'Curva de aprendizado', data, borderColor: SERIES_ACCENT }],
      }}
    />
  )
}

function CompileErrorRatePanel({ agg }: { agg: EdaAggregate }) {
  if (isEmpty(agg)) return <EmptyState kind="eda" />
  const { labels, data } = points(agg)
  return (
    <Bar
      data={{
        labels,
        datasets: [{ label: 'Taxa de erro de compilação', data, backgroundColor: SERIES_NAVY }],
      }}
    />
  )
}

export function EdaCharts({ eda }: { eda: EdaResponse }) {
  return (
    <section>
      <h3>Análise exploratória (EDA)</h3>
      <SuccessRatePanel agg={eda.success_rate} />
      <LearningCurvePanel agg={eda.learning_curve} />
      <CompileErrorRatePanel agg={eda.compile_error_rate} />
    </section>
  )
}
