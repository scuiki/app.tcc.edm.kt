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

const NAVY = '#004479'
const ACCENT = '#0a5cff'
const SURFACE = '#ffffff'
const SURFACE_MUTED = '#f4f7fb'
const BORDER = '#e2e8f0'
const TEXT_MUTED = '#64748b'

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
    <div style={{ minHeight: '100vh', background: SURFACE_MUTED, color: '#0f172a' }}>
      <Header />
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0' }}>
        <Rail
          query={assignmentsQuery}
          selectedId={assignmentId}
          onSelect={(id) => setAssignmentId(id)}
        />
        <main style={{ flex: 1, padding: '24px' }}>
          <TabSwitch active={tab} onChange={setTab} />
          <section style={{ marginTop: '24px' }}>
            {assignmentId == null ? (
              <EmptyState kind="no-assignments" />
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

function Header() {
  return (
    <header
      role="banner"
      style={{
        background: NAVY,
        color: '#fff',
        display: 'flex',
        alignItems: 'center',
        gap: '16px',
        padding: '16px 24px',
      }}
    >
      <img src={FACENS_LOGO} alt="uniFacens" height={40} />
      <h1 style={{ fontSize: '20px', fontWeight: 600, margin: 0 }}>
        Dashboard de Domínio da Turma
      </h1>
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
    <nav
      aria-label="Turma / Assignment"
      style={{
        width: '260px',
        minHeight: 'calc(100vh - 72px)',
        background: SURFACE,
        borderRight: `1px solid ${BORDER}`,
        padding: '16px',
      }}
    >
      <p style={{ color: TEXT_MUTED, fontSize: '14px', margin: '0 0 8px' }}>Turma / Assignment</p>
      {query.isPending ? (
        <Loading />
      ) : query.isError ? (
        <ErrorState />
      ) : query.data.assignments.length === 0 ? (
        <EmptyState kind="no-assignments" />
      ) : (
        <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
          {query.data.assignments.map((a) => {
            const active = a.id === selectedId
            return (
              <li key={a.id}>
                <button
                  type="button"
                  onClick={() => onSelect(a.id)}
                  aria-current={active ? 'true' : undefined}
                  {...focusRing}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    minHeight: '40px',
                    padding: '8px 12px',
                    border: 'none',
                    cursor: 'pointer',
                    background: active ? ACCENT : 'transparent',
                    color: active ? '#fff' : '#0f172a',
                    fontWeight: active ? 600 : 400,
                    borderRadius: '6px',
                  }}
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
    <div role="tablist" style={{ display: 'flex', gap: '8px', borderBottom: `1px solid ${BORDER}` }}>
      {TABS.map((t) => {
        const selected = t.id === active
        return (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={selected}
            onClick={() => onChange(t.id)}
            {...focusRing}
            style={{
              minHeight: '40px',
              padding: '8px 16px',
              border: 'none',
              cursor: 'pointer',
              background: 'transparent',
              color: selected ? ACCENT : '#0f172a',
              fontWeight: selected ? 600 : 400,
              borderBottom: selected ? `2px solid ${ACCENT}` : '2px solid transparent',
            }}
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
    <div>
      {/* DASH-05: the uncertainty frame is ALWAYS rendered above the grid — never suppressed. */}
      <UncertaintyFrame firstAuc={data.first_auc} trainedAt={data.trained_at} />
      <HeatmapGrid matrix={data.matrix} firstAuc={data.first_auc} />
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
