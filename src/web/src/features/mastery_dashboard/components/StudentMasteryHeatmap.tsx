import { formatPercent } from '../../../lib/format'
import type { StudentMastery } from '../api/useMastery'
import { classifyMasteryLevel, type MasteryLevel } from '../masteryLevel'
import { DashboardEmptyState } from './DashboardEmptyState'

const FILL: Record<MasteryLevel, string> = {
  low: 'var(--band-low)',
  medium: 'var(--band-medium)',
  high: 'var(--band-high)',
}
// A palavra da faixa acompanha a cor, porque cor sozinha não basta para quem não distingue
const LEVEL_WORD: Record<MasteryLevel, string> = { low: 'Baixo', medium: 'Médio', high: 'Alto' }
const LEGEND = 'Baixo (<40%) · Médio (40–70%) · Alto (>70%)'

type CellIndex = Map<string, StudentMastery>

interface StudentMasteryHeatmapProps {
  matrix: StudentMastery[]
  firstAttemptAuc: number | null
}

export function StudentMasteryHeatmap({ matrix, firstAttemptAuc }: StudentMasteryHeatmapProps) {
  // Sem modelo e sem células é não treinado, e nunca uma grade toda vermelha de domínio zero
  if (firstAttemptAuc == null && matrix.length === 0) {
    return <DashboardEmptyState kind="mastery-untrained" />
  }
  const studentIds = [...new Set(matrix.map((cell) => cell.student_id))]
  const kcIds = [...new Set(matrix.map((cell) => cell.kc_id))]
  const cellAt: CellIndex = new Map(
    matrix.map((cell) => [`${cell.student_id}:${cell.kc_id}`, cell]),
  )
  return (
    <div className="heatmap">
      <div
        role="grid"
        className="heatmap__grid"
        style={{ gridTemplateColumns: `auto repeat(${kcIds.length}, minmax(2.5rem, 1fr))` }}
      >
        <span role="columnheader" />
        {kcIds.map((kcId) => (
          <span key={kcId} role="columnheader" className="mono">
            {kcId}
          </span>
        ))}
        {studentIds.map((studentId) => (
          <HeatmapRow key={studentId} studentId={studentId} kcIds={kcIds} cellAt={cellAt} />
        ))}
      </div>
      <p className="t-support">{LEGEND}</p>
    </div>
  )
}

interface HeatmapRowProps {
  studentId: string
  kcIds: number[]
  cellAt: CellIndex
}

function HeatmapRow({ studentId, kcIds, cellAt }: HeatmapRowProps) {
  return (
    <>
      <span role="rowheader" className="mono">
        {studentId}
      </span>
      {kcIds.map((kcId) => (
        <HeatmapCell key={kcId} cell={cellAt.get(`${studentId}:${kcId}`)} />
      ))}
    </>
  )
}

function HeatmapCell({ cell }: { cell: StudentMastery | undefined }) {
  if (!cell) return <span role="gridcell" aria-label="sem dado" />
  const level = classifyMasteryLevel(cell.mastery)
  const cue = `${LEVEL_WORD[level]} ${formatPercent(cell.mastery)}`
  return (
    <span
      role="gridcell"
      tabIndex={0}
      aria-label={cue}
      title={cue}
      className="heatmap__cell"
      style={{ background: FILL[level] }}
    />
  )
}
