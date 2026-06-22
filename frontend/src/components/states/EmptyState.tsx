// Empty states. A single discriminated `kind` selects the locked copy pair (no boolean-prop
// proliferation — react-composition-patterns). All four strings are verbatim from the UI-SPEC
// Copywriting Contract; "untrained" variants are a single locked sentence, the data-absent variants
// carry a heading + body. Rendered as plain JSX text (React auto-escapes); no raw-HTML injection (V5).

export type EmptyKind = 'no-assignments' | 'eda' | 'mastery-untrained' | 'recs-untrained'

interface EmptyCopy {
  heading?: string
  body: string
}

const COPY: Record<EmptyKind, EmptyCopy> = {
  'no-assignments': {
    heading: 'Nenhum assignment disponível',
    body: 'Suba e processe um dataset ProgSnap2 para que os assignments apareçam aqui.',
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
    <div role="status">
      {copy.heading ? <p>{copy.heading}</p> : null}
      <p>{copy.body}</p>
    </div>
  )
}
