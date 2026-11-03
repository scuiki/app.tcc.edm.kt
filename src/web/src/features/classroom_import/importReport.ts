import type {
  AssignmentTrainability,
  ClassroomImportReport,
  DetectedUpload,
  ImportCheck,
} from './api/classroomImport'

// Como o professor lê o resultado, e só o processado sem falha grava na turma
export type ImportOutcome = 'imported' | 'busy' | 'refused'

export function outcomeOf(report: ClassroomImportReport): ImportOutcome {
  if (report.checks.some((check) => check.check === 'another_job_running')) return 'busy'
  return report.has_fatal ? 'refused' : 'imported'
}

// O título em pt-BR de cada código, e a mensagem do backend vem embaixo como veio
const CHECK_TITLES: Record<string, string> = {
  orphan_codestate: 'Eventos sem código descartados',
  score_coercion: 'Notas não numéricas ignoradas',
  few_problems: 'Poucos problemas num exercício',
  small_sample: 'Poucos alunos num exercício',
  encoding: 'A tabela não está em UTF-8',
  missing_required_column: 'A tabela de eventos está incompleta',
  another_job_running: 'Outro processo está rodando',
}

export function checkTitle(check: ImportCheck): string {
  const fallback =
    check.severity === 'fatal' ? 'Uma verificação obrigatória falhou' : 'Aviso do processamento'
  return CHECK_TITLES[check.check] ?? fallback
}

export function fatalChecksOf(report: ClassroomImportReport): ImportCheck[] {
  return report.checks.filter((check) => check.severity === 'fatal')
}

// Os avisos não impedem a importação, só registram o que o sistema ajustou ou recomenda cautela
export function warningsOf(report: ClassroomImportReport): ImportCheck[] {
  // O Compile repetido junto do Run.Program é o formato do ProgSnap2, então não vira aviso
  return report.checks.filter(
    (check) => check.severity !== 'fatal' && check.check !== 'dedup_compile',
  )
}

// O caminho dentro do pacote, sem a pasta do servidor onde ele foi extraído
export function pathInUpload(path: string, upload: DetectedUpload): string {
  const prefix = upload.raw_dir.endsWith('/') ? upload.raw_dir : `${upload.raw_dir}/`
  return path.startsWith(prefix) ? path.slice(prefix.length) : path
}

// O que falta no pacote para processar, na ordem em que o professor precisa corrigir
export type MissingTable = 'main_table' | 'code_snapshots'

export function missingTableOf(upload: DetectedUpload): MissingTable | null {
  if (upload.main_tables.length === 0) return 'main_table'
  if (upload.code_snapshots == null) return 'code_snapshots'
  return null
}

export function readinessSentence(assignments: AssignmentTrainability[]): string {
  const ready = assignments.filter((assignment) => assignment.trainable).length
  const total = assignments.length
  if (ready === 0) {
    return 'Nenhum exercício tem acertos e erros suficientes para treinar, e só as estatísticas ficam disponíveis.'
  }
  if (ready === total) {
    return total === 1
      ? 'O exercício está pronto para a extração de conceitos.'
      : `Os ${total} exercícios estão prontos para a extração de conceitos.`
  }
  return `${ready} dos ${total} exercícios estão prontos para a extração de conceitos.`
}
