// student × KC heatmap (DASH-01): a hand-built CSS grid, not a chart — the signal is 3 discrete bands
// and the DOM grid carries the dual-axis labels, the mandatory non-color cue, and ARIA more robustly
// (UI-SPEC Interaction Contract). It only colors backend-authored mastery; it never recomputes (D-08).

import type { MasteryCell } from '../api/schema'
import { band, type Band } from '../lib/bands'
import { formatPercent } from '../lib/format'
import { EmptyState } from './states/EmptyState'

const FILL: Record<Band, string> = { low: '#DC2626', medium: '#F59E0B', high: '#16A34A' }

// Band word for the non-color cue, matching the legend wording (Pitfall 6 — the cell must not be
// color-only; a color-vision-deficient teacher reads the word + percent).
const BAND_WORD: Record<Band, string> = { low: 'Baixo', medium: 'Médio', high: 'Alto' }

const LEGEND = 'Baixo (<40%) · Médio (40–70%) · Alto (>70%)'

interface Props {
  matrix: MasteryCell[]
  firstAuc: number | null
}

export function HeatmapGrid({ matrix, firstAuc }: Props) {
  // Untrained == no published model AND no cells; mirrors masteryViewState so an empty matrix can never
  // paint an all-red zero grid (Pitfall 2). Inlined (vs. importing the discriminator) to avoid faking a
  // full MasteryResponse for a two-field check.
  if (firstAuc == null && matrix.length === 0) {
    return <EmptyState kind="mastery-untrained" />
  }

  const subjects = [...new Set(matrix.map((c) => c.student_id))]
  const kcs = [...new Set(matrix.map((c) => c.kc_id))]
  const cellAt = new Map(matrix.map((c) => [`${c.student_id}:${c.kc_id}`, c]))

  return (
    <div className="stack-lg">
      <Grid subjects={subjects} kcs={kcs} cellAt={cellAt} />
      <Legend />
    </div>
  )
}

function Grid({
  subjects,
  kcs,
  cellAt,
}: {
  subjects: string[]
  kcs: number[]
  cellAt: Map<string, MasteryCell>
}) {
  return (
    <div
      role="grid"
      style={{
        display: 'grid',
        gridTemplateColumns: `auto repeat(${kcs.length}, minmax(2.5rem, 1fr))`,
        gap: '2px',
      }}
    >
      <span role="columnheader" />
      {kcs.map((kc) => (
        <span key={`h-${kc}`} role="columnheader" className="mono">
          {kc}
        </span>
      ))}
      {subjects.map((subject) => (
        <Row key={subject} subject={subject} kcs={kcs} cellAt={cellAt} />
      ))}
    </div>
  )
}

function Row({
  subject,
  kcs,
  cellAt,
}: {
  subject: string
  kcs: number[]
  cellAt: Map<string, MasteryCell>
}) {
  return (
    <>
      <span role="rowheader" className="mono">
        {subject}
      </span>
      {kcs.map((kc) => {
        const cell = cellAt.get(`${subject}:${kc}`)
        if (!cell) return <span key={`${subject}:${kc}`} role="gridcell" aria-label="sem dado" />
        const b = band(cell.mastery)
        const cue = `${BAND_WORD[b]} ${formatPercent(cell.mastery)}`
        return (
          // focus-visible ring (UI-SPEC): cells are focusable for keyboard inspection; outline is
          // restored on focus, never removed without replacement.
          <span
            key={`${subject}:${kc}`}
            role="gridcell"
            tabIndex={0}
            aria-label={cue}
            title={cue}
            style={{ background: FILL[b], minHeight: '2.5rem' }}
          />
        )
      })}
    </>
  )
}

function Legend() {
  return <p className="t-label" style={{ color: 'var(--color-text-muted)', margin: 0 }}>{LEGEND}</p>
}
