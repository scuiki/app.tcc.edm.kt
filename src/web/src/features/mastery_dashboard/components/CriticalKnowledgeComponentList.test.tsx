import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { CriticalKnowledgeComponentList } from './CriticalKnowledgeComponentList'

describe('CriticalKnowledgeComponentList', () => {
  it('keeps the backend order, weakest first', () => {
    render(
      <CriticalKnowledgeComponentList
        kcs={[
          { kc_id: 7, mean_mastery: 0.2 },
          { kc_id: 3, mean_mastery: 0.35 },
        ]}
      />,
    )
    expect(screen.getByText('KCs críticos da turma')).toBeInTheDocument()
    const items = screen.getAllByRole('listitem')
    expect(within(items[0]).getByText('7', { exact: true })).toBeInTheDocument()
    expect(within(items[1]).getByText('3', { exact: true })).toBeInTheDocument()
  })

  it('shows the mean mastery as a percent', () => {
    render(<CriticalKnowledgeComponentList kcs={[{ kc_id: 7, mean_mastery: 0.2 }]} />)
    expect(screen.getByText('20%')).toBeInTheDocument()
  })
})
