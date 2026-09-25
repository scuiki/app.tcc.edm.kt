import { ApiError } from '../../http/client'
import type { AssignmentStatus } from '../assignments/api/useAssignments'
import type { GenerationJob, ProblemKnowledgeComponents } from './api/knowledgeComponents'

// Um conceito do exercício com os problemas que ele marca
export interface KnowledgeComponentUsage {
  id: number
  name: string
  problemIds: number[]
}

// A lista de conceitos sai invertendo a de problemas, sem pedir outra rota à api
export function knowledgeComponentsOf(
  problems: ProblemKnowledgeComponents[],
): KnowledgeComponentUsage[] {
  const byId = new Map<number, KnowledgeComponentUsage>()
  for (const problem of problems) {
    for (const kc of problem.knowledge_components) {
      const usage = byId.get(kc.id) ?? { id: kc.id, name: kc.name, problemIds: [] }
      usage.problemIds.push(problem.problem_id)
      byId.set(kc.id, usage)
    }
  }
  return [...byId.values()].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR'))
}

// Com '5, 12 e 233' e não '5, 12, 233', como se escreve em pt-BR
export function listProblemIds(problemIds: number[]): string {
  if (problemIds.length <= 1) return problemIds.join('')
  return `${problemIds.slice(0, -1).join(', ')} e ${problemIds[problemIds.length - 1]}`
}

export function problemCount(count: number): string {
  return count === 1 ? '1 problema' : `${count} problemas`
}

// Os problemas que o conceito mantido marca depois de mesclar, sem repetir e em ordem
export function mergedProblemIds(keep: KnowledgeComponentUsage, drop: KnowledgeComponentUsage) {
  return [...new Set([...keep.problemIds, ...drop.problemIds])].sort((a, b) => a - b)
}

// Os problemas em que este é o único conceito, e que ficariam sem nenhum se ele saísse
export function problemsOnlyMarkedBy(
  kcId: number,
  problems: ProblemKnowledgeComponents[],
): number[] {
  return problems
    .filter(
      (problem) =>
        problem.knowledge_components.length === 1 && problem.knowledge_components[0].id === kcId,
    )
    .map((problem) => problem.problem_id)
}

// O backend também barra, e quando barra a mensagem dele vem junto, como veio
export function editErrorText(error: Error): string {
  if (error instanceof ApiError && error.status === 409 && error.detail) {
    return `A mudança foi recusada. ${error.detail}`
  }
  return 'Não foi possível salvar. Verifique se a API está no ar e tente de novo.'
}

export const ASSIGNMENT_STATUS_LABEL: Record<AssignmentStatus, string> = {
  statistics_only: 'Só estatísticas',
  ready_for_kc_generation: 'Pronto para conceitos',
  kc_draft: 'Rascunho de conceitos',
  kc_approved: 'Conceitos aprovados',
  trained: 'Modelo treinado',
}

// Só o rascunho e o aprovado se editam, e o treinado fica para consulta para não divergir do modelo
export function isEditable(status: AssignmentStatus | null | undefined): boolean {
  return status === 'kc_draft' || status === 'kc_approved'
}

export function hasKnowledgeComponents(status: AssignmentStatus | null | undefined): boolean {
  return isEditable(status) || status === 'trained'
}

// Os três estágios que o job informa, na ordem em que roda
export const GENERATION_STAGES = [
  { stage: 'generate', label: 'Identificando os conceitos de cada problema' },
  { stage: 'cluster', label: 'Agrupando os conceitos parecidos e nomeando cada grupo' },
  { stage: 'qmatrix', label: 'Ligando os conceitos aos problemas' },
] as const

export type StageState = 'done' | 'current' | 'todo'

export function stageStateOf(stage: string, job: GenerationJob | undefined): StageState {
  if (job?.status === 'done') return 'done'
  const order = GENERATION_STAGES.map((item) => item.stage as string)
  const current = job?.stage ? order.indexOf(job.stage) : -1
  const index = order.indexOf(stage)
  if (current === -1) return index === 0 && job?.status === 'running' ? 'current' : 'todo'
  if (index < current) return 'done'
  return index === current ? 'current' : 'todo'
}
