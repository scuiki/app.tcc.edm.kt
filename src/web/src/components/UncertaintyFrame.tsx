// Uncertainty frame (DASH-05/D-08): the mastery view's epistemic guardrail. It is derived from two
// fields present in EVERY mastery response (first_attempt_auc, trained_at) and MUST always render — never
// suppressed, never collapsed into a bare number — so an untrained model is never read as a verdict.

import { formatPercent } from '../lib/format'

interface Props {
  firstAuc: number | null
  trainedAt: string | null
}

export function UncertaintyFrame({ firstAuc, trainedAt }: Props) {
  // Tinted info banner (not a thick one-side border): trained carries a faint accent tint, untrained a
  // neutral muted tone. The role and copy are unchanged.
  const tone = firstAuc == null ? 'uframe uframe--untrained' : 'uframe uframe--trained'
  return (
    <div role="note" className={tone}>
      {firstAuc == null ? <Untrained /> : <Trained firstAuc={firstAuc} trainedAt={trainedAt} />}
    </div>
  )
}

function Trained({ firstAuc, trainedAt }: { firstAuc: number; trainedAt: string | null }) {
  // Verbatim from the UI-SPEC Copywriting Contract; rendered as JSX text (auto-escaped), no raw HTML.
  return (
    <p>
      Sinal com incerteza — AUC da turma {formatPercent(firstAuc)}, dados de {trainedAt}. Não é um
      veredito.
    </p>
  )
}

function Untrained() {
  return <p>Modelo ainda não treinado para este assignment. A EDA abaixo está disponível mesmo assim.</p>
}
