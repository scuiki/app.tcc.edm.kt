import type { StageState } from '../../components/ui/StageList'
import type { TrainingJob } from '../model_training/api/training'

// Os três estágios que o diálogo mostra; as épocas são a menor parte do tempo do treino
export const TRAINING_STAGES = [
  { stage: 'preparing', label: 'Preparando o código dos alunos' },
  { stage: 'training', label: 'Treinando o modelo' },
  { stage: 'publishing', label: 'Avaliando e publicando' },
] as const

export type TrainingStage = (typeof TRAINING_STAGES)[number]['stage']

// O job só informa a época; antes da primeira está preparando, depois da última está publicando
export function currentStageOf(job: TrainingJob | undefined): TrainingStage | null {
  if (!job || job.status === 'pending') return 'preparing'
  if (job.status !== 'running') return null
  if (job.current_epoch == null) return 'preparing'
  if (job.total_epochs != null && job.current_epoch >= job.total_epochs) return 'publishing'
  return 'training'
}

export function stageStateOf(stage: TrainingStage, job: TrainingJob | undefined): StageState {
  if (job?.status === 'done') return 'done'
  const current = currentStageOf(job)
  if (current == null) return 'todo'
  const order = TRAINING_STAGES.map((item) => item.stage as TrainingStage)
  const index = order.indexOf(stage)
  const currentIndex = order.indexOf(current)
  if (index < currentIndex) return 'done'
  return index === currentIndex ? 'current' : 'todo'
}

// O texto da época, só enquanto o estágio de treino está rodando
export function epochProgress(job: TrainingJob | undefined): string | null {
  if (currentStageOf(job) !== 'training' || job?.current_epoch == null) return null
  return `época ${job.current_epoch} de ${job.total_epochs ?? '?'}`
}
