import { describe, expect, it } from 'vitest'

import type { TrainingJob } from '../model_training/api/training'
import { epochProgress, stageStateOf } from './trainingStages'

function job(partial: Partial<TrainingJob>): TrainingJob {
  return {
    job_id: 7,
    status: 'running',
    current_epoch: null,
    total_epochs: null,
    train_loss: null,
    error_message: null,
    java_parse_rate: null,
    ...partial,
  }
}

const states = (current: TrainingJob | undefined) =>
  (['preparing', 'training', 'publishing'] as const).map((stage) => stageStateOf(stage, current))

describe('training stages', () => {
  it('is preparing before the first epoch, even before the job answers', () => {
    expect(states(undefined)).toEqual(['current', 'todo', 'todo'])
    expect(states(job({ status: 'pending' }))).toEqual(['current', 'todo', 'todo'])
    expect(states(job({ status: 'running' }))).toEqual(['current', 'todo', 'todo'])
  })

  it('is training while the epochs advance and publishing after the last one', () => {
    expect(states(job({ current_epoch: 12, total_epochs: 40 }))).toEqual([
      'done',
      'current',
      'todo',
    ])
    expect(states(job({ current_epoch: 40, total_epochs: 40 }))).toEqual([
      'done',
      'done',
      'current',
    ])
  })

  it('marks everything done when the job is done and nothing when it failed', () => {
    expect(states(job({ status: 'done', current_epoch: 40, total_epochs: 40 }))).toEqual([
      'done',
      'done',
      'done',
    ])
    expect(states(job({ status: 'failed', current_epoch: 3, total_epochs: 40 }))).toEqual([
      'todo',
      'todo',
      'todo',
    ])
  })

  it('shows the epoch only during training', () => {
    expect(epochProgress(job({ current_epoch: 12, total_epochs: 40 }))).toBe('época 12 de 40')
    expect(epochProgress(job({ current_epoch: 40, total_epochs: 40 }))).toBeNull()
    expect(epochProgress(job({}))).toBeNull()
  })
})
