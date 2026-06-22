// Teacher dashboard shell (D-02/D-03): navy Facens header + assignment rail + Mastery/EDA/Recs tab
// switch, wiring the Plan 03/04 components to the four query hooks. Two pieces of view state are lifted
// here — the selected assignment id and the active tab (react-composition-patterns: explicit variants,
// not boolean-prop sprawl). The SPA only formats backend-authored values; no recomputation (D-08), and
// all copy/text is rendered as auto-escaped JSX — never raw HTML injection (T-06.1-15).

import { useState } from 'react'

// Vendored brand asset in public/ (06.1-FACENS-BRAND): referenced by its served root path, not bundled
// — never hotlinked from the WordPress upload.
const FACENS_LOGO = '/facens-logo.png'

import { AtRiskList } from './components/AtRiskList'
import { CriticalKCList } from './components/CriticalKCList'
import { EdaCharts } from './components/EdaCharts'
import { HeatmapGrid } from './components/HeatmapGrid'
import { RecommendationList } from './components/RecommendationList'
import { UncertaintyFrame } from './components/UncertaintyFrame'
import { EmptyState } from './components/states/EmptyState'
import { ErrorState } from './components/states/ErrorState'
import { Loading } from './components/states/Loading'
import { useAssignments } from './hooks/useAssignments'
import { useEda } from './hooks/useEda'
import { useMastery } from './hooks/useMastery'
import { useRecommendations } from './hooks/useRecommendations'

// Explicit tab variants — the discriminant that routes the main region, never a pile of booleans.
type Tab = 'mastery' | 'eda' | 'recs'

const TABS: { id: Tab; label: string }[] = [
  { id: 'mastery', label: 'Domínio (mastery)' },
  { id: 'eda', label: 'Análise exploratória' },
  { id: 'recs', label: 'Recomendações de reforço' },
]

const ACCENT = '#0a5cff'

// Shared focus ring so every interactive control shows the accent outline (UI-SPEC: never outline:none
// without a replacement). Applied via onFocus/onBlur to keep it inline without a CSS file.
const focusRing = {
  onFocus: (e: React.FocusEvent<HTMLElement>) => {
    e.currentTarget.style.outline = `2px solid ${ACCENT}`
    e.currentTarget.style.outlineOffset = '2px'
  },
  onBlur: (e: React.FocusEvent<HTMLElement>) => {
    e.currentTarget.style.outline = 'none'
  },
}

function App() {
  const [assignmentId, setAssignmentId] = useState<number | null>(null)
  const [tab, setTab] = useState<Tab>('mastery')

  const assignmentsQuery = useAssignments()

  return (
    <div className="app-shell">
      <Header />
      <div className="app-body">
        <Rail
          query={assignmentsQuery}
          selectedId={assignmentId}
          onSelect={(id) => setAssignmentId(id)}
        />
        <main className="app-main">
          <TabSwitch active={tab} onChange={setTab} />
          <section className="content">
            {assignmentId == null ? (
              <NothingSelected query={assignmentsQuery} />
            ) : tab === 'mastery' ? (
              <MasteryTab assignmentId={assignmentId} />
            ) : tab === 'eda' ? (
              <EdaTab assignmentId={assignmentId} />
            ) : (
              <RecsTab assignmentId={assignmentId} />
            )}
          </section>
        </main>
      </div>
    </div>
  )
}

// Defect fix: with nothing selected, the main region must distinguish two cases the old code conflated.
// A populated list → "pick one". The empty-list / pending / error states are already surfaced by the
// rail, so the main region stays quiet to avoid repeating the same message in two places.
function NothingSelected({ query }: { query: ReturnType<typeof useAssignments> }) {
  if (query.isPending || query.isError) return null
  if (query.data.assignments.length === 0) return null
  return <EmptyState kind="select-assignment" />
}

function Header() {
  return (
    <header role="banner" className="app-header">
      <img className="app-header__logo" src={FACENS_LOGO} alt="uniFacens" height={40} />
      <h1 className="app-header__title t-display">Dashboard de Domínio da Turma</h1>
    </header>
  )
}

function Rail({
  query,
  selectedId,
  onSelect,
}: {
  query: ReturnType<typeof useAssignments>
  selectedId: number | null
  onSelect: (id: number) => void
}) {
  return (
    <nav aria-label="Turma / Assignment" className="rail">
      <p className="rail__label">Turma / Assignment</p>
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState />
      ) : query.data.assignments.length === 0 ? (
        <EmptyState kind="no-assignments" />
      ) : (
        <ul className="rail__list">
          {query.data.assignments.map((a) => {
            const active = a.id === selectedId
            return (
              <li key={a.id}>
                <button
                  type="button"
                  className="rail__item"
                  onClick={() => onSelect(a.id)}
                  aria-current={active ? 'true' : undefined}
                  {...focusRing}
                >
                  {a.name}
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </nav>
  )
}

function TabSwitch({ active, onChange }: { active: Tab; onChange: (t: Tab) => void }) {
  return (
    <div role="tablist" className="tabs">
      {TABS.map((t) => {
        const selected = t.id === active
        return (
          <button
            key={t.id}
            type="button"
            role="tab"
            className="tabs__tab"
            aria-selected={selected}
            onClick={() => onChange(t.id)}
            {...focusRing}
          >
            {t.label}
          </button>
        )
      })}
    </div>
  )
}

function MasteryTab({ assignmentId }: { assignmentId: number }) {
  const { data, isPending, isError } = useMastery(assignmentId)
  if (isPending) return <Loading />
  if (isError) return <ErrorState />
  return (
    // Rhythm: uncertainty banner on top, then the heatmap, then the two lists — each its own region with
    // generous separation. Surfaces are selective (the grid + lists sit on panels; the banner does not).
    <div className="stack-xl">
      {/* DASH-05: the uncertainty frame is ALWAYS rendered above the grid — never suppressed. */}
      <UncertaintyFrame firstAuc={data.first_auc} trainedAt={data.trained_at} />
      <div className="panel">
        <HeatmapGrid matrix={data.matrix} firstAuc={data.first_auc} />
      </div>
      <CriticalKCList criticalKcs={data.critical_kcs} />
      <AtRiskList atRiskStudents={data.at_risk_students} />
    </div>
  )
}

function EdaTab({ assignmentId }: { assignmentId: number }) {
  const { data, isPending, isError } = useEda(assignmentId)
  if (isPending) return <Loading />
  if (isError) return <ErrorState />
  return <EdaCharts eda={data} />
}

function RecsTab({ assignmentId }: { assignmentId: number }) {
  const { data, isPending, isError } = useRecommendations(assignmentId)
  if (isPending) return <Loading />
  if (isError) return <ErrorState />
  return <RecommendationList recommendations={data.recommendations} />
}

export default App
