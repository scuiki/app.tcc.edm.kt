import { fireEvent, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, renderWithClient } from '../../../test/renderWithClient'
import type { AssignmentStatus, AssignmentSummary } from '../../assignments/api/useAssignments'
import type { ClassroomSummary } from '../../classrooms/api/classrooms'
import type { Mastery, StudentDetail, SubmissionStatistics } from '../api/masteryDashboard'
import { MasteryDashboardPage } from './MasteryDashboardPage'

const CLASSROOM: ClassroomSummary = {
  id: 1,
  name: 'CSEDM Spring 2019',
  created_at: '2026-06-21T22:07:00+00:00',
  problem_count: 50,
  student_count: 413,
  status: 'in_progress',
}

function assignment(id: number, progsnapId: number, status: AssignmentStatus): AssignmentSummary {
  return {
    id,
    progsnap_assignment_id: progsnapId,
    name: `Assignment ${progsnapId}`,
    status,
    published_model_id: status === 'trained' ? 5 : null,
  }
}

const LOOPS = { kc_id: 1, kc_name: 'Laços' }
const IFS = { kc_id: 2, kc_name: 'Condicionais' }

// Dois problemas do 439, o 13 difícil e o 12 fácil, com os conceitos já aprovados
function statistics(assignmentId: number, withConcepts: boolean): SubmissionStatistics {
  return {
    assignment_id: assignmentId,
    student_count: 386,
    problems: [
      {
        problem_id: 13,
        success_rate: 0.124,
        median_attempts_to_complete: 5,
        students_attempted: 386,
        students_completed: 355,
        compile_errors_per_run: 2.43,
        kcs: withConcepts ? [LOOPS, IFS] : [],
      },
      {
        problem_id: 12,
        success_rate: 0.475,
        median_attempts_to_complete: null,
        students_attempted: 362,
        students_completed: 0,
        compile_errors_per_run: 0.62,
        kcs: withConcepts ? [IFS] : [],
      },
    ],
    knowledge_components: withConcepts
      ? [
          { kc_id: 1, kc_name: 'Laços', problem_ids: [13], success_rate: 0.168, runs: 4705 },
          {
            kc_id: 2,
            kc_name: 'Condicionais',
            problem_ids: [12, 13],
            success_rate: 0.29,
            runs: 5785,
          },
        ]
      : [],
  }
}

const HISTOGRAM = [8, 129, 107, 64, 49, 29, 0, 0, 0, 0]

function mastery(assignmentId: number, trained: boolean): Mastery {
  if (!trained)
    return { assignment_id: assignmentId, model: null, knowledge_components: [], problems: [] }
  return {
    assignment_id: assignmentId,
    model: {
      version_number: 5,
      trained_at: '2026-08-12T03:11:13.749266+00:00',
      student_count: 386,
      problem_count: 2,
      knowledge_component_count: 2,
    },
    knowledge_components: [
      { kc_id: 1, kc_name: 'Laços', problem_ids: [13], mean_mastery: 0.276, histogram: HISTOGRAM },
      {
        kc_id: 2,
        kc_name: 'Condicionais',
        problem_ids: [12, 13],
        mean_mastery: 0.41,
        histogram: HISTOGRAM,
      },
    ],
    problems: [
      { problem_id: 13, mean_mastery: 0.405, histogram: HISTOGRAM, kcs: [LOOPS, IFS] },
      { problem_id: 12, mean_mastery: 0.664, histogram: HISTOGRAM, kcs: [IFS] },
    ],
  }
}

const STUDENTS = [
  {
    student_id: '14316',
    mean_mastery: 0.187,
    completed: 7,
    attempted: 10,
    weakest_kcs: [{ kc_id: 1, kc_name: 'Laços', mastery: 0.085 }],
  },
  {
    student_id: '10004',
    mean_mastery: 0.52,
    completed: 10,
    attempted: 10,
    weakest_kcs: [{ kc_id: 2, kc_name: 'Condicionais', mastery: 0.3 }],
  },
]

const STUDENT_DETAIL: StudentDetail = {
  student_id: '14316',
  mean_mastery: 0.187,
  completed: 7,
  attempted: 10,
  runs: 107,
  compile_errors: 237,
  knowledge_components: [
    { kc_id: 1, kc_name: 'Laços', mastery: 0.085 },
    { kc_id: 2, kc_name: 'Condicionais', mastery: 0.3 },
  ],
  problems: [
    { problem_id: 13, mastery: 0.1 },
    { problem_id: 12, mastery: 0.27 },
  ],
}

const ASSIGNMENTS = [
  assignment(1, 439, 'trained'),
  assignment(2, 487, 'kc_approved'),
  assignment(3, 492, 'kc_draft'),
  assignment(4, 502, 'statistics_only'),
]

function fakeApi() {
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const path = String(input)
    if (path === '/classrooms') return jsonResponse({ classrooms: [CLASSROOM] })
    if (path.startsWith('/assignments?classroom_id='))
      return jsonResponse({ assignments: ASSIGNMENTS })
    const match = path.match(/^\/mastery-dashboard\/(\d+)\/(.+)$/)
    if (match) {
      const id = Number(match[1])
      const route = match[2]
      if (route === 'submission-statistics') return jsonResponse(statistics(id, id <= 2))
      if (route === 'mastery') return jsonResponse(mastery(id, id === 1))
      if (route === 'students')
        return jsonResponse({ assignment_id: id, students: id === 1 ? STUDENTS : [] })
      if (route === 'students/14316') return jsonResponse(STUDENT_DETAIL)
    }
    throw new Error(`fetch inesperado ${path}`)
  })
}

afterEach(() => {
  window.location.hash = ''
  vi.restoreAllMocks()
})

function renderAssignment(id: number) {
  fakeApi()
  renderWithClient(<MasteryDashboardPage classroomId={1} assignmentId={id} />)
}

describe('MasteryDashboardPage, the exercise in the address', () => {
  it('shows the path with the status of the exercise named in the address', async () => {
    renderAssignment(1)
    const path = await screen.findByRole('navigation', { name: 'Caminho' })
    expect(path).toHaveTextContent('Turmas›CSEDM Spring 2019›Assignment 439›Análise')
    expect(path).toHaveTextContent('Modelo treinado')
  })

  it('says the exercise was not found for an unknown id', async () => {
    renderAssignment(99)
    expect(await screen.findByText('Exercício não encontrado')).toBeInTheDocument()
  })
})

describe('MasteryDashboardPage, the situation of the exercise', () => {
  it('says why a statistics only exercise never trains, and shows only what happened', async () => {
    renderAssignment(4)
    expect(await screen.findByText(/não treina um modelo/)).toBeInTheDocument()
    const table = await screen.findByRole('table', { name: 'Problemas' })
    expect(within(table).queryByRole('columnheader', { name: /Domínio/ })).not.toBeInTheDocument()
  })

  it('points to the concepts of this exercise while nothing is approved', async () => {
    renderAssignment(3)
    const link = await screen.findByRole('link', { name: 'Ir para Conceitos' })
    expect(link).toHaveAttribute('href', '#/classrooms/1/assignments/3/knowledge-components')
    fireEvent.click(screen.getByRole('tab', { name: 'Conceitos' }))
    expect(screen.getByText(/depois de aprovados/)).toBeInTheDocument()
  })

  it('offers the training once the concepts are approved, and the concepts tab has them', async () => {
    renderAssignment(2)
    expect(await screen.findByRole('button', { name: 'Treinar modelo' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: 'Conceitos' }))
    const table = await screen.findByRole('table', { name: 'Conceitos' })
    expect(within(table).getByText('Laços')).toBeInTheDocument()
    fireEvent.mouseEnter(within(table).getByRole('button', { name: /1 problema/ }))
    expect(screen.getByRole('tooltip')).toHaveTextContent('evidência fraca')
    fireEvent.click(within(table).getByRole('button', { name: '2 problemas' }))
    expect(within(table).getByText('Problema 12')).toBeInTheDocument()
    expect(within(table).getByText('Problema 13')).toBeInTheDocument()
    expect(within(table).queryByRole('columnheader', { name: /Domínio/ })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: 'Alunos' }))
    expect(screen.getByText(/depois de treinar/)).toBeInTheDocument()
  })
})

describe('MasteryDashboardPage, what happened', () => {
  it('lists the problems from the lowest success rate up, with the numbers of each', async () => {
    renderAssignment(1)
    const table = await screen.findByRole('table', { name: 'Problemas' })
    const names = () =>
      within(table)
        .getAllByRole('button', { name: /^Problema \d+$/ })
        .map((b) => b.textContent)
    expect(names()).toEqual(['Problema 13', 'Problema 12'])
    const hard = within(table).getByRole('button', { name: 'Problema 13' }).closest('tr')!
    expect(
      within(hard).getByRole('img', { name: 'Taxa de acerto do problema 13 12%' }),
    ).toBeInTheDocument()
    expect(within(hard).getByText('2,43')).toBeInTheDocument()
    expect(within(hard).getByText('355')).toBeInTheDocument()
    const easy = within(table).getByRole('button', { name: 'Problema 12' }).closest('tr')!
    expect(within(easy).getByText('—')).toBeInTheDocument()
  })

  it('sorts in memory when a column header is clicked, and flips on the second click', async () => {
    renderAssignment(1)
    const table = await screen.findByRole('table', { name: 'Problemas' })
    const names = () =>
      within(table)
        .getAllByRole('button', { name: /^Problema \d+$/ })
        .map((b) => b.textContent)
    fireEvent.click(within(table).getByRole('button', { name: 'Taxa de acerto' }))
    expect(names()).toEqual(['Problema 12', 'Problema 13'])
    expect(within(table).getByRole('columnheader', { name: /Taxa de acerto/ })).toHaveAttribute(
      'aria-sort',
      'descending',
    )
    fireEvent.click(within(table).getByRole('button', { name: 'Taxa de acerto' }))
    expect(names()).toEqual(['Problema 13', 'Problema 12'])
  })

  it('opens the concepts of a problem with the arrow next to its name', async () => {
    renderAssignment(1)
    const table = await screen.findByRole('table', { name: 'Problemas' })
    const arrow = within(table).getByRole('button', { name: 'Problema 13' })
    expect(arrow).toHaveAttribute('aria-expanded', 'false')
    expect(within(table).queryByText('Laços')).not.toBeInTheDocument()
    fireEvent.click(arrow)
    expect(arrow).toHaveAttribute('aria-expanded', 'true')
    expect(within(table).getByText('Laços')).toBeInTheDocument()
    expect(within(table).getByRole('img', { name: 'Conceitos' })).toBeInTheDocument()
  })
})

describe('MasteryDashboardPage, what the model estimates', () => {
  it('adds the estimated columns with the mark, and names the exercise in the title', async () => {
    renderAssignment(1)
    const table = await screen.findByRole('table', { name: 'Problemas' })
    const header = within(table).getByRole('columnheader', { name: /Domínio/ })
    expect(within(header).getByRole('img', { name: 'Dado estimado' })).toBeInTheDocument()
    const hard = within(table).getByRole('button', { name: 'Problema 13' }).closest('tr')!
    expect(
      await within(hard).findByRole('img', { name: 'Domínio estimado no problema 13 41%' }),
    ).toBeInTheDocument()
    expect(
      within(hard).getByRole('figure', { name: 'Distribuição dos alunos no problema 13' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { level: 1, name: 'Assignment 439' })).toBeInTheDocument()
    expect(screen.queryByText(/Fonte:/)).not.toBeInTheDocument()
    expect(
      screen.getByText(/dados estimados pelo modelo de aprendizado de máquina/),
    ).toBeInTheDocument()
  })

  it('lists the students, sortable, and opens the detail of one on click', async () => {
    renderAssignment(1)
    fireEvent.click(await screen.findByRole('tab', { name: 'Alunos' }))
    const table = await screen.findByRole('table', { name: 'Alunos' })
    const ids = () =>
      within(table)
        .getAllByRole('row')
        .slice(1)
        .map((row) => row.querySelector('td')?.textContent)
    expect(ids()).toEqual(['14316', '10004'])
    expect(within(table).getByText('Laços (9%)')).toBeInTheDocument()
    fireEvent.click(within(table).getByRole('button', { name: 'Completou' }))
    fireEvent.click(within(table).getByRole('button', { name: 'Completou' }))
    expect(ids()).toEqual(['10004', '14316'])

    fireEvent.click(within(table).getByText('14316'))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByRole('heading', { name: 'Aluno 14316' })).toBeInTheDocument()
    expect(await within(dialog).findByText('107')).toBeInTheDocument()
    expect(within(dialog).getByRole('img', { name: 'Problema 13 10%' })).toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Fechar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
