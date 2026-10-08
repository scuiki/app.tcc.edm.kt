import { fireEvent, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { AssignmentSummary } from '../features/assignments/api/useAssignments'
import type { ClassroomSummary } from '../features/classrooms/api/classrooms'
import { jsonResponse, renderWithClient } from '../test/renderWithClient'
import { SideMenu } from './SideMenu'

const CLASSROOMS: ClassroomSummary[] = [
  {
    id: 1,
    name: 'CSEDM Spring 2019',
    created_at: '2026-06-21T22:07:00+00:00',
    problem_count: 50,
    student_count: 413,
    status: 'trained',
  },
  {
    id: 7,
    name: 'Turma 7',
    created_at: '2026-09-01T10:00:00+00:00',
    problem_count: 10,
    student_count: 30,
    status: 'in_progress',
  },
]

const ASSIGNMENTS: Record<number, AssignmentSummary[]> = {
  1: [
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
      status: 'kc_approved',
      published_model_id: null,
    },
    {
      id: 3,
      progsnap_assignment_id: 492,
      name: 'Assignment 492',
      status: 'kc_draft',
      published_model_id: null,
    },
    {
      id: 4,
      progsnap_assignment_id: 494,
      name: 'Assignment 494',
      status: 'statistics_only',
      published_model_id: null,
    },
  ],
  7: [],
}

function fakeApi() {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const path = String(input)
    if (path === '/classrooms') return jsonResponse({ classrooms: CLASSROOMS })
    const match = path.match(/^\/assignments\?classroom_id=(\d+)$/)
    if (match) return jsonResponse({ assignments: ASSIGNMENTS[Number(match[1])] ?? [] })
    throw new Error(`fetch inesperado ${path}`)
  })
}

afterEach(() => {
  vi.restoreAllMocks()
  window.localStorage.clear()
})

describe('SideMenu', () => {
  it('keeps the classrooms closed under Turmas away from them, and opens them with the plus', async () => {
    fakeApi()
    renderWithClient(<SideMenu path="/classroom-imports" params={{}} />)

    const classrooms = screen.getByRole('link', { name: 'Turmas' })
    expect(classrooms).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('link', { name: 'CSEDM Spring 2019' })).not.toBeInTheDocument()
    fireEvent.click(classrooms)
    expect(classrooms).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(classrooms.querySelector('.side-menu__sign')!)
    expect(classrooms).toHaveAttribute('aria-expanded', 'true')
    const classroom = await screen.findByRole('link', { name: 'CSEDM Spring 2019' })
    expect(classroom).toHaveAttribute('href', '#/classrooms/1')
    expect(screen.queryByText('Assignment 439')).not.toBeInTheDocument()

    fireEvent.click(classroom)
    expect(classroom).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(classroom.querySelector('.side-menu__sign')!)
    const exercise = (await screen.findByText('Assignment 439')).closest('button')!
    expect(within(exercise).getByLabelText('Treinado')).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Análise' })).not.toBeInTheDocument()

    fireEvent.click(exercise)
    expect(screen.getByRole('link', { name: 'Análise' })).toHaveAttribute(
      'href',
      '#/classrooms/1/assignments/1/analysis',
    )
    expect(screen.getByRole('link', { name: 'Conceitos' })).toHaveAttribute(
      'href',
      '#/classrooms/1/assignments/1/knowledge-components',
    )
  })

  it('opens the classroom and the exercise of the current address and marks the screen', async () => {
    fakeApi()
    renderWithClient(
      <SideMenu
        path="/classrooms/1/assignments/2/knowledge-components"
        params={{ classroomId: 1, assignmentId: 2 }}
      />,
    )

    const links = await screen.findAllByRole('link', { name: 'Conceitos' })
    expect(links).toHaveLength(1)
    expect(links[0]).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('link', { name: 'CSEDM Spring 2019' })).toHaveAttribute(
      'aria-expanded',
      'true',
    )
  })

  it('marks each exercise with its status dot, and the one that never trains with none', async () => {
    fakeApi()
    renderWithClient(
      <SideMenu
        path="/classrooms/1/assignments/1/analysis"
        params={{ classroomId: 1, assignmentId: 1 }}
      />,
    )

    const row = async (name: string) => (await screen.findByText(name)).closest('button')!
    expect(within(await row('Assignment 439')).getByLabelText('Treinado')).toBeInTheDocument()
    expect(
      within(await row('Assignment 487')).getByLabelText('Conceitos aprovados'),
    ).toBeInTheDocument()
    // O rascunho divide com o pronto para conceitos o ponto vazio
    expect(
      within(await row('Assignment 492')).getByLabelText('Aguardando conceitos'),
    ).toBeInTheDocument()
    expect(within(await row('Assignment 494')).queryByRole('img')).not.toBeInTheDocument()
  })

  it('says when an open classroom has no exercises', async () => {
    fakeApi()
    window.localStorage.setItem(
      'edmkt.menu.expanded',
      JSON.stringify(['classrooms', 'classroom:7']),
    )
    renderWithClient(<SideMenu path="/classrooms/7" params={{ classroomId: 7 }} />)

    expect(await screen.findByText('Sem exercícios')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Turma 7' })).toHaveAttribute('aria-current', 'page')
  })

  it('only navigates when a classroom is chosen, and its sign opens and closes it', async () => {
    fakeApi()
    window.localStorage.setItem('edmkt.menu.expanded', JSON.stringify(['classrooms']))
    renderWithClient(<SideMenu path="/classrooms" params={{}} />)
    const classroom = await screen.findByRole('link', { name: 'CSEDM Spring 2019' })

    fireEvent.click(classroom)
    expect(classroom).toHaveAttribute('aria-expanded', 'false')

    const sign = classroom.querySelector('.side-menu__sign')!
    fireEvent.click(sign)
    expect(classroom).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(sign)
    expect(classroom).toHaveAttribute('aria-expanded', 'false')
  })

  it('remembers what the address opened after leaving it', async () => {
    fakeApi()
    const first = renderWithClient(
      <SideMenu
        path="/classrooms/1/assignments/1/analysis"
        params={{ classroomId: 1, assignmentId: 1 }}
      />,
    )
    expect(await screen.findByRole('link', { name: 'Análise' })).toBeInTheDocument()
    first.unmount()

    renderWithClient(<SideMenu path="/classroom-imports" params={{}} />)
    expect(await screen.findByText('Assignment 439')).toBeInTheDocument()
  })

  it('remembers what was opened in the browser', async () => {
    fakeApi()
    window.localStorage.setItem('edmkt.menu.expanded', JSON.stringify(['classrooms']))
    const first = renderWithClient(<SideMenu path="/classrooms" params={{}} />)
    const classroom = await screen.findByRole('link', { name: 'Turma 7' })
    fireEvent.click(classroom.querySelector('.side-menu__sign')!)
    expect(await screen.findByText('Sem exercícios')).toBeInTheDocument()
    first.unmount()

    renderWithClient(<SideMenu path="/classrooms" params={{}} />)
    expect(await screen.findByText('Sem exercícios')).toBeInTheDocument()
  })
})
