import { describe, expect, it } from 'vitest'

import { formatCount, formatDate, formatDateTime, formatPercent } from './format'

describe('formatPercent', () => {
  it('renders integer percentages', () => {
    expect(formatPercent(0.76)).toBe('76%')
    expect(formatPercent(0.0)).toBe('0%')
    expect(formatPercent(1.0)).toBe('100%')
  })

  it('rounds half up, like the backend', () => {
    expect(formatPercent(0.765)).toBe('77%')
  })

  it('returns a placeholder for a missing value instead of NaN%', () => {
    expect(formatPercent(null)).toBe('—')
    expect(formatPercent(undefined)).toBe('—')
  })
})

describe('formatCount', () => {
  it('groups thousands with a dot', () => {
    expect(formatCount(131943)).toBe('131.943')
    expect(formatCount(413)).toBe('413')
  })
})

describe('formatDate and formatDateTime', () => {
  // Meio-dia em UTC cai no mesmo dia em qualquer fuso do Brasil
  const iso = '2026-09-24T12:00:00+00:00'

  it('formats the date as dd/mm/yyyy', () => {
    expect(formatDate(iso)).toBe('24/09/2026')
  })

  it('formats date and time without the comma', () => {
    expect(formatDateTime(iso)).toMatch(/^24\/09\/2026 \d{2}:\d{2}$/)
  })
})
