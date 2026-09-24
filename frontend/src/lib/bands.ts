// Mirrors classify_mastery_level (src/api/mastery_dashboard/domain/mastery_level.py) — classifies a backend-authored mastery value, never
// recomputes it (D-08). Cutoffs are duplicated here as the single client-side source of truth; if the
// core ever moves them, bands.test.ts breaks and forces this file back into sync.

export const BAND_LOW = 0.4
export const BAND_HIGH = 0.7

export type Band = 'low' | 'medium' | 'high'

// 0.70 is INCLUSIVE in medium (<= BAND_HIGH), matching classify_band — not the < trap (Pitfall 3).
export function band(mastery: number): Band {
  if (mastery < BAND_LOW) return 'low'
  if (mastery <= BAND_HIGH) return 'medium'
  return 'high'
}
