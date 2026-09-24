import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { StudentsAtRiskList } from './StudentsAtRiskList'

describe('StudentsAtRiskList', () => {
  it('renders the heading and each student id as a list item', () => {
    render(<StudentsAtRiskList studentIds={['s1', 's2']} />)
    expect(screen.getByText('Alunos em atenção')).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
    expect(screen.getByText('s1')).toBeInTheDocument()
  })

  it('renders an empty list without throwing', () => {
    render(<StudentsAtRiskList studentIds={[]} />)
    expect(screen.queryAllByRole('listitem')).toHaveLength(0)
  })
})
