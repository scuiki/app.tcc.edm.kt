import { EmptyState } from '../../../components/states/states'

// Cada situação vazia do dashboard com o seu texto, para as telas não repetirem as frases
export type DashboardEmptyKind =
  | 'no-assignments'
  | 'select-assignment'
  | 'pre-training-statistics'
  | 'mastery-untrained'
  | 'recommendations-untrained'

const COPY: Record<DashboardEmptyKind, { title?: string; text: string }> = {
  'no-assignments': {
    title: 'Nenhum assignment disponível',
    text: 'Suba e processe um dataset ProgSnap2 para que os assignments apareçam aqui.',
  },
  'select-assignment': {
    title: 'Selecione um assignment',
    text: 'Escolha uma turma na lista à esquerda para ver domínio, análise exploratória e recomendações.',
  },
  'pre-training-statistics': {
    title: 'Sem dados para análise ainda',
    text: 'Conclua a ingestão de um dataset desta turma para ver taxa de acerto, curvas de aprendizado e erros de compilação.',
  },
  'mastery-untrained': {
    text: 'Sem heatmap de domínio até o treino do Code-DKT concluir. Veja a EDA enquanto isso.',
  },
  'recommendations-untrained': {
    text: 'As recomendações de reforço aparecem após o treino, a partir dos KCs de menor domínio.',
  },
}

export function DashboardEmptyState({ kind }: { kind: DashboardEmptyKind }) {
  return <EmptyState {...COPY[kind]} />
}
