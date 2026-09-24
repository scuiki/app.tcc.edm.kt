import { describe, expect, it } from 'vitest'

import { formatPercent } from './format'

// Mirrors the backend's {:.0%} convention (integer percent) so the SPA never disagrees with a
// backend-authored number. Rounding is pinned to Math.round (round half up): 0.765 -> "77%".

describe('formatPercent', () => {
  it('renders integer percentages', () => {
    expect(formatPercent(0.76)).toBe('76%')
    expect(formatPercent(0.5)).toBe('50%')
    expect(formatPercent(0.0)).toBe('0%')
    expect(formatPercent(1.0)).toBe('100%')
  })

  it('rounds to the nearest integer percent (half up)', () => {
    expect(formatPercent(0.765)).toBe('77%')
  })

  it('returns a placeholder for null/undefined instead of NaN%', () => {
    expect(formatPercent(null)).toBe('—')
    expect(formatPercent(undefined)).toBe('—')
  })
})
