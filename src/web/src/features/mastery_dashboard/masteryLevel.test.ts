import { describe, expect, it } from 'vitest'

import { classifyMasteryLevel, HIGH_LEVEL_CUTOFF, LOW_LEVEL_CUTOFF } from './masteryLevel'

describe('classifyMasteryLevel', () => {
  it('classifies low below the low cutoff', () => {
    expect(classifyMasteryLevel(0.0)).toBe('low')
    expect(classifyMasteryLevel(0.39)).toBe('low')
  })

  it('treats 0.40 as the inclusive lower edge of medium', () => {
    expect(classifyMasteryLevel(0.4)).toBe('medium')
  })

  it('classifies interior medium values', () => {
    expect(classifyMasteryLevel(0.55)).toBe('medium')
  })

  it('treats 0.70 as medium, not high', () => {
    expect(classifyMasteryLevel(0.7)).toBe('medium')
  })

  it('classifies high above the high cutoff', () => {
    expect(classifyMasteryLevel(0.7000001)).toBe('high')
    expect(classifyMasteryLevel(1.0)).toBe('high')
  })

  it('uses the backend cutoffs', () => {
    expect(LOW_LEVEL_CUTOFF).toBe(0.4)
    expect(HIGH_LEVEL_CUTOFF).toBe(0.7)
  })
})
