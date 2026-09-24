import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ClassroomSummary } from '../api/classrooms'
import { RecentActivityCard } from './RecentActivityCard'

function classroom(id: number, createdAt: string): ClassroomSummary {
  return {
    id,
    name: `Turma ${id}`,
    created_at: createdAt,
    problem_count: 0,
    student_count: 0,
    status: 'awaiting_data',
  }
}

describe('RecentActivityCard', () => {
  it('shows at most five creations, newest first', () => {
    const classrooms = [1, 2, 3, 4, 5, 6].map((id) =>
      classroom(id, `2026-09-0${id}T12:00:00+00:00`),
    )
    render(<RecentActivityCard classrooms={classrooms} />)
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(5)
    expect(items[0]).toHaveTextContent('Turma 6 foi criada')
    expect(items[4]).toHaveTextContent('Turma 2 foi criada')
  })

  it('shows the creation date and time', () => {
    render(<RecentActivityCard classrooms={[classroom(1, '2026-09-24T12:00:00+00:00')]} />)
    expect(screen.getByText(/^24\/09\/2026 \d{2}:\d{2}$/)).toBeInTheDocument()
  })
})
