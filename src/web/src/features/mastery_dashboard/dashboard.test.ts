import { describe, expect, it } from 'vitest'

import {
  dashboardStateOf,
  hasApprovedConcepts,
  listProblemIds,
  mergeConcepts,
  mergeProblems,
  problemCount,
} from './dashboard'

describe('dashboardStateOf', () => {
  it('maps every situation of the exercise to what the screen shows', () => {
    expect(dashboardStateOf('statistics_only')).toBe('not_trainable')
    expect(dashboardStateOf('ready_for_kc_generation')).toBe('no_approved_concepts')
    expect(dashboardStateOf('kc_draft')).toBe('no_approved_concepts')
    expect(dashboardStateOf('kc_approved')).toBe('ready_to_train')
    expect(dashboardStateOf('trained')).toBe('trained')
    expect(dashboardStateOf(null)).toBe('no_approved_concepts')
  })

  it('only approved or trained exercises have concepts to show', () => {
    expect(hasApprovedConcepts('ready_to_train')).toBe(true)
    expect(hasApprovedConcepts('trained')).toBe(true)
    expect(hasApprovedConcepts('no_approved_concepts')).toBe(false)
    expect(hasApprovedConcepts('not_trainable')).toBe(false)
  })
})

describe('text helpers', () => {
  it('counts problems in the singular and the plural', () => {
    expect(problemCount(1)).toBe('1 problema')
    expect(problemCount(9)).toBe('9 problemas')
  })

  it('lists problem ids the way pt-BR writes a list', () => {
    expect(listProblemIds([3])).toBe('3')
    expect(listProblemIds([3, 13])).toBe('3 e 13')
    expect(listProblemIds([13, 235, 236])).toBe('13, 235 e 236')
  })
})

describe('merging what happened with what the model estimates', () => {
  const problem = {
    problem_id: 13,
    success_rate: 0.12,
    median_attempts_to_complete: 5,
    students_attempted: 386,
    students_completed: 355,
    compile_errors_per_run: 2.43,
    kcs: [],
  }
  const concept = { kc_id: 10, kc_name: 'Laços', problem_ids: [13], success_rate: 0.17, runs: 4705 }

  it('adds the estimate to the problems that have one and leaves the others without', () => {
    const rows = mergeProblems(
      [problem, { ...problem, problem_id: 12 }],
      [{ problem_id: 13, mean_mastery: 0.4, histogram: [1, 2], kcs: [] }],
    )
    expect(rows[0]).toMatchObject({ problem_id: 13, mean_mastery: 0.4, histogram: [1, 2] })
    expect(rows[1]).toMatchObject({ problem_id: 12, mean_mastery: null, histogram: null })
  })

  it('does the same for concepts', () => {
    const rows = mergeConcepts(
      [concept],
      [{ kc_id: 10, kc_name: 'Laços', problem_ids: [13], mean_mastery: 0.28, histogram: [3] }],
    )
    expect(rows[0]).toMatchObject({ kc_id: 10, mean_mastery: 0.28, histogram: [3] })
    expect(mergeConcepts([concept], [])[0].mean_mastery).toBeNull()
  })
})
