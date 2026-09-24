// Formats backend-authored floats as integer percents, matching the backend {:.0%} convention so the
// SPA never renders a number that disagrees with its source (D-08). No recomputation here.

const PLACEHOLDER = '—'

// null/undefined (e.g. an untrained first_attempt_auc) renders the placeholder, never "NaN%".
export function formatPercent(value: number | null | undefined): string {
  if (value == null) return PLACEHOLDER
  return `${Math.round(value * 100)}%`
}
