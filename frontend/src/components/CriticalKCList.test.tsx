import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CriticalKCList } from './CriticalKCList'
import type { CriticalKC } from '../api/schema'

// DASH-02: the backend authors critical_kcs weakest-first; the client renders that order verbatim and
// NEVER re-sorts (D-08). The order assertion is the tripwire against a client-side ranking recompute.

describe('CriticalKCList', () => {
  it('renders the heading and items in the backend array order (7 before 3, no reorder)', () => {
    const kcs: CriticalKC[] = [
      { kc_id: 7, mean_mastery: 0.2 },
      { kc_id: 3, mean_mastery: 0.35 },
    ]
    render(<CriticalKCList criticalKcs={kcs} />)
    expect(screen.getByText('KCs críticos da turma')).toBeInTheDocument()

    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    // Exact match: the kc_id span is its own node, so "3" must not collide with the "35%" mastery.
    expect(within(items[0]).getByText('7', { exact: true })).toBeInTheDocument()
    expect(within(items[1]).getByText('3', { exact: true })).toBeInTheDocument()
  })

  it('shows mean_mastery as a percent', () => {
    const kcs: CriticalKC[] = [{ kc_id: 7, mean_mastery: 0.2 }]
    render(<CriticalKCList criticalKcs={kcs} />)
    expect(screen.getByText(/20%/)).toBeInTheDocument()
  })
})
