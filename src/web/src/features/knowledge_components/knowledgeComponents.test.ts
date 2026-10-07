import { describe, expect, it } from 'vitest'

import { ApiError } from '../../http/client'
import type { GenerationJob } from './api/knowledgeComponents'
import {
  editErrorText,
  isEditable,
  knowledgeComponentsOf,
  listProblemIds,
  mergedProblemIds,
  problemCount,
  problemsOnlyMarkedBy,
  stageStateOf,
  GENERATION_STAGES,
} from './knowledgeComponents'

const LOOPS = { id: 1, name: 'Laços' }
const IFS = { id: 2, name: 'Condicionais' }

describe('knowledgeComponentsOf', () => {
  it('inverts problems into concepts with the problems each one marks, by name', () => {
    const usages = knowledgeComponentsOf([
      { problem_id: 5, description: null, knowledge_components: [LOOPS, IFS] },
      { problem_id: 12, description: null, knowledge_components: [LOOPS] },
      { problem_id: 20, description: null, knowledge_components: [] },
    ])
    expect(usages).toEqual([
      { id: 2, name: 'Condicionais', problemIds: [5] },
      { id: 1, name: 'Laços', problemIds: [5, 12] },
    ])
  })
})

describe('listProblemIds and problemCount', () => {
  it('lists with a final e, as written in pt-BR', () => {
    expect(listProblemIds([5])).toBe('5')
    expect(listProblemIds([5, 12])).toBe('5 e 12')
    expect(listProblemIds([5, 12, 233])).toBe('5, 12 e 233')
  })

  it('counts problems in the singular and plural', () => {
    expect(problemCount(1)).toBe('1 problema')
    expect(problemCount(3)).toBe('3 problemas')
  })
})

describe('mergedProblemIds', () => {
  it('joins the problems of both without repeating', () => {
    const keep = { id: 1, name: 'A', problemIds: [5, 12, 233] }
    const drop = { id: 2, name: 'B', problemIds: [12, 235] }
    expect(mergedProblemIds(keep, drop)).toEqual([5, 12, 233, 235])
  })
})

describe('isEditable', () => {
  it('lets only the draft and the approved be edited', () => {
    expect(isEditable('kc_draft')).toBe(true)
    expect(isEditable('kc_approved')).toBe(true)
    expect(isEditable('trained')).toBe(false)
    expect(isEditable('ready_for_kc_generation')).toBe(false)
  })
})

describe('stageStateOf', () => {
  const job = (status: GenerationJob['status'], stage: string | null): GenerationJob => ({
    job_id: 1,
    status,
    stage,
    error_message: null,
    progress_done: null,
    progress_total: null,
  })

  it('marks the stages before the current one as done', () => {
    expect(stageStateOf('generate', job('running', 'cluster'))).toBe('done')
    expect(stageStateOf('cluster', job('running', 'cluster'))).toBe('current')
    expect(stageStateOf('qmatrix', job('running', 'cluster'))).toBe('todo')
  })

  it('starts on the first stage while running without a stage yet', () => {
    expect(stageStateOf('generate', job('running', null))).toBe('current')
    expect(stageStateOf('generate', job('pending', null))).toBe('todo')
  })

  it('marks every stage as done when the job is done', () => {
    expect(stageStateOf('translate', job('done', 'translate'))).toBe('done')
  })

  it('knows the evidence and the translation, the last two stages', () => {
    expect(GENERATION_STAGES.map((item) => item.stage)).toEqual([
      'generate',
      'cluster',
      'qmatrix',
      'evidence',
      'translate',
    ])
    expect(stageStateOf('qmatrix', job('running', 'evidence'))).toBe('done')
    expect(stageStateOf('evidence', job('running', 'evidence'))).toBe('current')
    expect(stageStateOf('translate', job('running', 'evidence'))).toBe('todo')
  })

  it('shows the five texts of the extraction, in the order the job runs them', () => {
    expect(GENERATION_STAGES.map((item) => item.label)).toEqual([
      'Identificando os conceitos de cada problema',
      'Agrupando os conceitos parecidos e nomeando cada grupo',
      'Ligando os conceitos aos problemas',
      'Apontando onde cada conceito aparece nas soluções',
      'Traduzindo os conceitos para o português',
    ])
  })

  it('shows a job done at an older stage as done, like the ones of the older classrooms', () => {
    const states = GENERATION_STAGES.map((item) => stageStateOf(item.stage, job('done', 'qmatrix')))
    expect(states).toEqual(GENERATION_STAGES.map(() => 'done'))
  })
})

describe('problemsOnlyMarkedBy', () => {
  it('finds the problems left without a concept if this one goes away', () => {
    const problems = [
      { problem_id: 5, description: null, knowledge_components: [LOOPS] },
      { problem_id: 12, description: null, knowledge_components: [LOOPS, IFS] },
      { problem_id: 20, description: null, knowledge_components: [IFS] },
    ]
    expect(problemsOnlyMarkedBy(1, problems)).toEqual([5])
    expect(problemsOnlyMarkedBy(2, problems)).toEqual([20])
  })
})

describe('editErrorText', () => {
  it('passes along the backend reason of a refusal', () => {
    expect(editErrorText(new ApiError(409, 'problema 5 ficaria com 0 KCs'))).toBe(
      'A mudança foi recusada. problema 5 ficaria com 0 KCs',
    )
  })

  it('points to the api for any other failure', () => {
    expect(editErrorText(new ApiError(503, ''))).toMatch(/Verifique se a API está no ar/)
  })
})
