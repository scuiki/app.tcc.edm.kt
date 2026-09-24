import { describe, expect, it } from 'vitest'

import { band, BAND_LOW, BAND_HIGH } from './bands'

// Mirrors classify_mastery_level
// (src/api/mastery_dashboard/domain/services/mastery_classification.py) exactly. The two
// boundaries are the contract: 0.40 enters medium (>= BAND_LOW) and 0.70 stays medium
// (<= BAND_HIGH) — Pitfall 3, the 0.70 trap.

describe('band', () => {
  it('classifies low below the low cutoff', () => {
    expect(band(0.0)).toBe('low')
    expect(band(0.39)).toBe('low')
  })

  it('treats 0.40 as the inclusive lower edge of medium', () => {
    expect(band(0.4)).toBe('medium')
  })

  it('classifies interior medium values', () => {
    expect(band(0.55)).toBe('medium')
  })

  it('treats 0.70 as medium (inclusive upper edge — Pitfall 3, not high)', () => {
    expect(band(0.7)).toBe('medium')
  })

  it('classifies high above the high cutoff', () => {
    expect(band(0.7000001)).toBe('high')
    expect(band(0.85)).toBe('high')
    expect(band(1.0)).toBe('high')
  })
})

describe('band cutoff constants', () => {
  it('mirror the core BAND_LOW / BAND_HIGH values', () => {
    expect(BAND_LOW).toBe(0.4)
    expect(BAND_HIGH).toBe(0.7)
  })
})
