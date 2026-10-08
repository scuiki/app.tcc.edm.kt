import { screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, renderWithClient } from '../../../test/renderWithClient'
import type { AssignmentSummary } from '../../assignments/api/useAssignments'
import type { ClassroomSummary } from '../api/classrooms'
import { ClassroomPage } from './ClassroomPage'

const CLASSROOM: ClassroomSummary = {
  id: 1,
  name: 'CSEDM Spring 2019',
  created_at: '2026-06-21T22:07:00+00:00',
  problem_count: 50,
  student_count: 413,
  status: 'trained',
}

const ASSIGNMENTS: AssignmentSummary[] = [
  {
    id: 1,
    progsnap_assignment_id: 439,
    name: 'Assignment 439',
    status: 'trained',
    published_model_id: 5,
  },
  {
    id: 2,
    progsnap_assignment_id: 487,
    name: 'Assignment 487',
    status: 'ready_for_kc_generation',
    published_model_id: null,
  },
]

function fakeApi(assignments = ASSIGNMENTS) {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const path = String(input)
    if (path === '/classrooms') return jsonResponse({ classrooms: [CLASSROOM] })
    if (path === '/assignments?classroom_id=1') return jsonResponse({ assignments })
    if (path === '/assignments?classroom_id=9') return jsonResponse({ assignments: [] })
    throw new Error(`fetch inesperado ${path}`)
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ClassroomPage', () => {
  it('shows the classroom with its exercises as cards, each with its screens', async () => {
    fakeApi()
    renderWithClient(<ClassroomPage classroomId={1} />)

    expect(await screen.findByRole('heading', { name: 'CSEDM Spring 2019' })).toBeInTheDocument()
    expect(
      screen.getByText(/413 alunos · 50 problemas · criada em 21\/06\/2026/),
    ).toBeInTheDocument()
    const card = screen.getByText('Assignment 439').closest('li')!
    expect(within(card).getByText('Treinado')).toBeInTheDocument()
    expect(within(card).getByRole('link', { name: 'Análise' })).toHaveAttribute(
      'href',
      '#/classrooms/1/assignments/1/analysis',
    )
    expect(within(card).getByRole('link', { name: 'Conceitos' })).toHaveAttribute(
      'href',
      '#/classrooms/1/assignments/1/knowledge-components',
    )
    expect(screen.getByRole('link', { name: 'Importar dados para esta turma' })).toHaveAttribute(
      'href',
      '#/classroom-imports?classroom=1',
    )
  })

  it('points to the import when the classroom has no exercises yet', async () => {
    fakeApi([])
    renderWithClient(<ClassroomPage classroomId={1} />)

    expect(await screen.findByText('Nenhum exercício ainda')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Importar dados' })).toHaveAttribute(
      'href',
      '#/classroom-imports?classroom=1',
    )
  })

  it('says the classroom was not found for an unknown id', async () => {
    fakeApi()
    renderWithClient(<ClassroomPage classroomId={9} />)

    expect(await screen.findByText('Turma não encontrada')).toBeInTheDocument()
  })
})
