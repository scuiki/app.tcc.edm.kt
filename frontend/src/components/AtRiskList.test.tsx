import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { AtRiskList } from './AtRiskList'

// DASH-03: at_risk_students is string[] of subject_ids (Pitfall 1 — NOT objects). Render as a plain
// list; an empty array is an empty list, never a crash.

describe('AtRiskList', () => {
  it('renders the heading and each subject id as a list item', () => {
    render(<AtRiskList atRiskStudents={['s1', 's2']} />)
    expect(screen.getByText('Alunos em atenção')).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(2)
    expect(screen.getByText('s1')).toBeInTheDocument()
    expect(screen.getByText('s2')).toBeInTheDocument()
  })

  it('renders an empty list for [] without throwing', () => {
    render(<AtRiskList atRiskStudents={[]} />)
    expect(screen.getByText('Alunos em atenção')).toBeInTheDocument()
    expect(screen.queryAllByRole('listitem')).toHaveLength(0)
  })
})
