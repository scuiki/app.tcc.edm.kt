// Empty states. A single discriminated `kind` selects the locked copy pair (no boolean-prop
// proliferation — react-composition-patterns). All four strings are verbatim from the UI-SPEC
// Copywriting Contract; "untrained" variants are a single locked sentence, the data-absent variants
// carry a heading + body. Rendered as plain JSX text (React auto-escapes); no raw-HTML injection (V5).

import { Inbox } from 'lucide-react'

export type EmptyKind =
  | 'no-assignments'
  | 'select-assignment'
  | 'eda'
  | 'mastery-untrained'
  | 'recs-untrained'

interface EmptyCopy {
  heading?: string
  body: string
}

const COPY: Record<EmptyKind, EmptyCopy> = {
  'no-assignments': {
    heading: 'Nenhum assignment disponível',
    body: 'Suba e processe um dataset ProgSnap2 para que os assignments apareçam aqui.',
  },
  // "Nothing selected yet" — distinct from no-assignments (the list exists, the teacher just hasn't
  // picked one). New copy: the UI-SPEC has no string for this state.
  'select-assignment': {
    heading: 'Selecione um assignment',
    body: 'Escolha uma turma na lista à esquerda para ver domínio, análise exploratória e recomendações.',
  },
  eda: {
    heading: 'Sem dados para análise ainda',
    body: 'Conclua a ingestão de um dataset desta turma para ver taxa de acerto, curvas de aprendizado e erros de compilação.',
  },
  'mastery-untrained': {
    body: 'Sem heatmap de domínio até o treino do Code-DKT concluir. Veja a EDA enquanto isso.',
  },
  'recs-untrained': {
    body: 'As recomendações de reforço aparecem após o treino, a partir dos KCs de menor domínio.',
  },
}

export function EmptyState({ kind }: { kind: EmptyKind }) {
  const copy = COPY[kind]
  return (
    <div role="status" className="state">
      <Inbox className="state__icon" size={18} aria-hidden="true" />
      <div className="state__body">
        {copy.heading ? <p className="state__heading">{copy.heading}</p> : null}
        <p className="state__text">{copy.body}</p>
      </div>
    </div>
  )
}
