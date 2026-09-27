import type { AssignmentStatus } from '../assignments/api/useAssignments'
import type {
  KnowledgeComponentMastery,
  KnowledgeComponentStatistics,
  ProblemMastery,
  ProblemStatistics,
} from './api/masteryDashboard'

// O que a tela mostra para o exercício, decidido só pela situação dele
export type DashboardState = 'not_trainable' | 'no_approved_concepts' | 'ready_to_train' | 'trained'

export function dashboardStateOf(status: AssignmentStatus | null | undefined): DashboardState {
  if (status === 'trained') return 'trained'
  if (status === 'kc_approved') return 'ready_to_train'
  if (status === 'statistics_only') return 'not_trainable'
  return 'no_approved_concepts'
}

// Os conceitos por taxa de acerto só existem depois de aprovados
export function hasApprovedConcepts(state: DashboardState): boolean {
  return state === 'ready_to_train' || state === 'trained'
}

export type AnalysisTab = 'problems' | 'concepts' | 'students'

export function problemCount(count: number): string {
  return count === 1 ? '1 problema' : `${count} problemas`
}

// Com '5, 12 e 233' e não '5, 12, 233', como se escreve em pt-BR
export function listProblemIds(problemIds: number[]): string {
  if (problemIds.length <= 1) return problemIds.join('')
  return `${problemIds.slice(0, -1).join(', ')} e ${problemIds[problemIds.length - 1]}`
}

// Uma linha da aba Problemas, o que aconteceu e, com modelo, o que ele estima
export interface ProblemRow extends ProblemStatistics {
  mean_mastery: number | null
  histogram: number[] | null
}

export function mergeProblems(
  statistics: ProblemStatistics[],
  mastery: ProblemMastery[],
): ProblemRow[] {
  const byId = new Map(mastery.map((problem) => [problem.problem_id, problem]))
  return statistics.map((problem) => {
    const estimated = byId.get(problem.problem_id)
    return {
      ...problem,
      mean_mastery: estimated?.mean_mastery ?? null,
      histogram: estimated?.histogram ?? null,
    }
  })
}

export interface ConceptRow extends KnowledgeComponentStatistics {
  // Em quantos problemas o conceito aparece, para ordenar a coluna
  recurrence: number
  mean_mastery: number | null
  histogram: number[] | null
}

export function mergeConcepts(
  statistics: KnowledgeComponentStatistics[],
  mastery: KnowledgeComponentMastery[],
): ConceptRow[] {
  const byId = new Map(mastery.map((kc) => [kc.kc_id, kc]))
  return statistics.map((kc) => {
    const estimated = byId.get(kc.kc_id)
    return {
      ...kc,
      recurrence: kc.problem_ids.length,
      mean_mastery: estimated?.mean_mastery ?? null,
      histogram: estimated?.histogram ?? null,
    }
  })
}

// Os textos que acompanham os números, os mesmos em toda a tela
export const ESTIMATED_HINT = 'Dado estimado'

export const MASTERY_HINT =
  'Domínio é a chance estimada pelo modelo de o aluno acertar, se tentasse agora, os problemas deste exercício. Não é a fração do conceito que ele já aprendeu, e o modelo não conhece problemas de outros exercícios.'

export const MEDIAN_ATTEMPTS_HINT = 'Mediana do número de tentativas por problema'

export const DISTRIBUTION_HINT =
  'Quantos alunos caem em cada faixa de 10 pontos do domínio, de 0 a 100%'
