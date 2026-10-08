import { describe, expect, it } from 'vitest'

import { ApiError } from '../../http/client'
import type { GenerationJob } from './api/knowledgeComponents'
import {
  cellClickOutcomeOf,
  editErrorText,
  factsLineCountsOf,
  isEditable,
  knowledgeComponentsOf,
  listProblemIds,
  problemCount,
  problemsOnlyMarkedBy,
  problemsWithoutKnowledgeComponent,
  stableKnowledgeComponentOrder,
  stageStateOf,
  GENERATION_STAGES,
} from './knowledgeComponents'

const LOOPS = { id: 1, name: 'Laços', is_generated_by_llm: true }
const IFS = { id: 2, name: 'Condicionais', is_generated_by_llm: true }
const RECURSION = { id: 3, name: 'Recursão', is_generated_by_llm: true }

// Um problema com os conceitos dados, sem enunciado e com acertos
function problem(problemId: number, knowledgeComponents: (typeof LOOPS)[]) {
  return {
    problem_id: problemId,
    statement: null,
    correct_run_count: 5,
    knowledge_components: knowledgeComponents,
  }
}

describe('knowledgeComponentsOf', () => {
  it('inverts problems into concepts with the problems each one marks, the most recurrent first', () => {
    const usages = knowledgeComponentsOf([
      problem(5, [LOOPS, IFS]),
      problem(12, [LOOPS]),
      { problem_id: 20, statement: null, correct_run_count: 0, knowledge_components: [] },
    ])
    expect(usages).toEqual([
      { id: 1, name: 'Laços', is_generated_by_llm: true, problemIds: [5, 12] },
      { id: 2, name: 'Condicionais', is_generated_by_llm: true, problemIds: [5] },
    ])
  })

  it('breaks a tie in recurrence by the name in pt-BR and then by the id', () => {
    const ARRAYS = { id: 7, name: 'Arrays', is_generated_by_llm: true }
    const ALGEBRA = { id: 9, name: 'Álgebra', is_generated_by_llm: false }
    const ALGEBRA_AGAIN = { id: 4, name: 'Álgebra', is_generated_by_llm: false }
    const usages = knowledgeComponentsOf([
      problem(5, [ARRAYS, ALGEBRA, ALGEBRA_AGAIN, LOOPS]),
      problem(12, [LOOPS]),
    ])
    // O Á vem antes do Ar em pt-BR, e não depois do Z, como na ordem dos códigos
    expect(usages.map((kc) => kc.id)).toEqual([1, 4, 9, 7])
  })
})

describe('stableKnowledgeComponentOrder', () => {
  it('takes the order of the first load', () => {
    const first = knowledgeComponentsOf([problem(5, [IFS, LOOPS]), problem(12, [LOOPS])])
    expect(stableKnowledgeComponentOrder([], first)).toEqual([1, 2])
  })

  it('keeps each concept in place when the recurrence changes', () => {
    // Condicionais passa a marcar dois problemas e Laços um só, e a ordem da primeira carga fica
    const reloaded = knowledgeComponentsOf([problem(5, [IFS, LOOPS]), problem(12, [IFS])])
    expect(reloaded.map((kc) => kc.id)).toEqual([2, 1])
    expect(stableKnowledgeComponentOrder([1, 2], reloaded)).toEqual([1, 2])
  })

  it('puts a new concept at the end and takes a removed one out', () => {
    const reloaded = knowledgeComponentsOf([
      problem(5, [RECURSION, LOOPS]),
      problem(12, [RECURSION]),
    ])
    expect(stableKnowledgeComponentOrder([1, 2], reloaded)).toEqual([1, 3])
  })

  it('gives back the same list when nothing came in or went out', () => {
    const previous = [1, 2]
    const reloaded = knowledgeComponentsOf([problem(5, [IFS, LOOPS]), problem(12, [IFS])])
    expect(stableKnowledgeComponentOrder(previous, reloaded)).toBe(previous)
  })
})

describe('cellClickOutcomeOf', () => {
  // O problema 12 só tem Laços, e a Recursão só marca o problema 20
  const problems = [problem(5, [LOOPS, IFS]), problem(12, [LOOPS]), problem(20, [IFS, RECURSION])]

  it('links an empty cell', () => {
    expect(cellClickOutcomeOf(3, 5, problems)).toBe('link')
  })

  it('unlinks right away when nothing is lost', () => {
    expect(cellClickOutcomeOf(1, 5, problems)).toBe('unlink')
  })

  it('refuses when the problem would be left without concept', () => {
    expect(cellClickOutcomeOf(1, 12, problems)).toBe('refused')
  })

  it('confirms when the concept would leave the exercise', () => {
    expect(cellClickOutcomeOf(3, 20, problems)).toBe('confirm')
  })

  it('refuses before confirming when both would happen', () => {
    // A Recursão só marca o problema 31, e ele só tem a Recursão
    expect(cellClickOutcomeOf(3, 31, [problem(5, [LOOPS]), problem(31, [RECURSION])])).toBe(
      'refused',
    )
  })
})

describe('factsLineCountsOf and problemsWithoutKnowledgeComponent', () => {
  const problems = [
    { problem_id: 5, statement: null, correct_run_count: 12, knowledge_components: [LOOPS, IFS] },
    { problem_id: 12, statement: null, correct_run_count: 9, knowledge_components: [LOOPS] },
    { problem_id: 20, statement: null, correct_run_count: 0, knowledge_components: [] },
    { problem_id: 31, statement: null, correct_run_count: 0, knowledge_components: [] },
  ]

  it('counts the problems, each concept once and the problems without concept', () => {
    expect(factsLineCountsOf(problems)).toEqual({
      problemCount: 4,
      knowledgeComponentCount: 2,
      problemsWithoutKnowledgeComponent: [20, 31],
    })
  })

  it('lists no problem when every one has a concept', () => {
    expect(problemsWithoutKnowledgeComponent(problems.slice(0, 2))).toEqual([])
  })

  it('counts zero concepts before the extraction', () => {
    expect(factsLineCountsOf(problems.slice(2))).toEqual({
      problemCount: 2,
      knowledgeComponentCount: 0,
      problemsWithoutKnowledgeComponent: [20, 31],
    })
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
      {
        problem_id: 5,
        statement: null,
        correct_run_count: 12,
        knowledge_components: [LOOPS],
      },
      {
        problem_id: 12,
        statement: null,
        correct_run_count: 9,
        knowledge_components: [LOOPS, IFS],
      },
      {
        problem_id: 20,
        statement: null,
        correct_run_count: 7,
        knowledge_components: [IFS],
      },
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
