import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, renderWithClient } from '../../../test/renderWithClient'
import type { AssignmentStatus, AssignmentSummary } from '../../assignments/api/useAssignments'
import type { ClassroomSummary } from '../../classrooms/api/classrooms'
import type { GenerationJob, ProblemKnowledgeComponents } from '../api/knowledgeComponents'
import { KnowledgeComponentsPage } from './KnowledgeComponentsPage'

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
    published_model_id: null,
  }
}

const LOOPS = { id: 1, name: 'Laços' }
const IFS = { id: 2, name: 'Condicionais' }
const RECURSION = { id: 3, name: 'Recursão' }

// O problema 12 só tem Laços, e a Recursão só marca o problema 20
function draftProblems(): ProblemKnowledgeComponents[] {
  return [
    { problem_id: 5, description: null, knowledge_components: [LOOPS, IFS] },
    { problem_id: 12, description: null, knowledge_components: [LOOPS] },
    { problem_id: 20, description: null, knowledge_components: [IFS, RECURSION] },
  ]
}

interface FakeApiOptions {
  classrooms?: ClassroomSummary[]
  job?: GenerationJob
  refuseStart?: boolean
}

// Uma api em memória, com os exercícios de uma turma e os conceitos de cada um
function fakeApi({ classrooms = [CLASSROOM], job, refuseStart = false }: FakeApiOptions = {}) {
  const assignments = [
    assignment(1, 439, 'kc_draft'),
    assignment(2, 487, 'ready_for_kc_generation'),
    assignment(3, 492, 'statistics_only'),
    assignment(4, 502, 'trained'),
  ]
  const problems: Record<number, ProblemKnowledgeComponents[]> = {
    1: draftProblems(),
    2: [{ problem_id: 17, description: null, knowledge_components: [] }],
    3: [],
    4: draftProblems(),
  }
  const statusOf = (id: number) => assignments.find((a) => a.id === id)!.status

  const spy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const path = String(input)
    const method = init?.method ?? 'GET'
    if (path === '/classrooms') return jsonResponse({ classrooms })
    if (path.startsWith('/assignments?classroom_id=')) return jsonResponse({ assignments })
    const problemsMatch = path.match(/^\/assignments\/(\d+)\/problems\/knowledge-components$/)
    if (problemsMatch) {
      const id = Number(problemsMatch[1])
      return jsonResponse({ assignment_id: id, status: statusOf(id), problems: problems[id] })
    }
    if (path === '/knowledge-components/generation-jobs' && method === 'POST') {
      if (refuseStart) return jsonResponse({ detail: 'já existe um job em andamento' }, 409)
      return jsonResponse({ job_id: 7, status: 'pending' }, 202)
    }
    if (path === '/knowledge-components/generation-jobs/7') {
      // Quando o job termina, o exercício 2 ganha conceitos e vira rascunho
      if (job?.status === 'done') {
        assignments[1] = { ...assignments[1], status: 'kc_draft' }
        problems[2] = [{ problem_id: 17, description: null, knowledge_components: [LOOPS] }]
      }
      return jsonResponse(job)
    }
    if (path === '/knowledge-components/approve') {
      assignments[0] = { ...assignments[0], status: 'kc_approved' }
      return jsonResponse({ assignment_id: 1, status: 'kc_approved' })
    }
    if (method !== 'GET') return jsonResponse({}, 200)
    throw new Error(`fetch inesperado ${method} ${path}`)
  })
  return spy
}

afterEach(() => {
  window.location.hash = ''
  vi.restoreAllMocks()
})

function calls(spy: ReturnType<typeof fakeApi>, method: string, path: string) {
  return spy.mock.calls.filter(([url, init]) => url === path && (init?.method ?? 'GET') === method)
}

async function openAssignment(name: string) {
  fireEvent.click(await screen.findByRole('button', { name: new RegExp(name) }))
}

describe('KnowledgeComponentsPage, choosing the exercise', () => {
  it('lists the exercises of the only classroom with their status', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage />)
    expect(await screen.findByRole('button', { name: /Assignment 439/ })).toHaveTextContent(
      'Rascunho de conceitos',
    )
    expect(screen.getByRole('button', { name: /Assignment 487/ })).toHaveTextContent(
      'Pronto para conceitos',
    )
    expect(screen.getByText('Escolha um exercício')).toBeInTheDocument()
  })

  it('takes the classroom from the hash, as when coming from the import', async () => {
    window.location.hash = '#/knowledge-components?classroom=1'
    fakeApi({ classrooms: [{ ...CLASSROOM, id: 9, name: 'Outra' }, CLASSROOM] })
    renderWithClient(<KnowledgeComponentsPage />)
    expect(await screen.findByRole('button', { name: /Assignment 439/ })).toBeInTheDocument()
    expect(screen.getByLabelText('Turma')).toHaveDisplayValue('CSEDM Spring 2019')
  })

  it('says there is nothing to extract from a statistics only exercise', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage />)
    await openAssignment('Assignment 492')
    expect(await screen.findByText('Não há conceitos para extrair')).toBeInTheDocument()
  })

  it('shows a trained exercise for reference only, with no edit and no approval', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage />)
    await openAssignment('Assignment 502')
    expect(await screen.findByText(/já tem modelo treinado/)).toBeInTheDocument()
    expect(screen.getAllByText('Laços').length).toBeGreaterThan(0)
    expect(screen.queryByRole('button', { name: /^Tirar / })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Adicionar conceito/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Editar o nome/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Aprovar/ })).not.toBeInTheDocument()
  })
})

describe('KnowledgeComponentsPage, extracting', () => {
  it('shows the running stages and does not let the dialog or the tab close', async () => {
    fakeApi({
      job: {
        job_id: 7,
        status: 'running',
        stage: 'cluster',
        error_message: null,
        progress_done: 3,
        progress_total: 8,
      },
    })
    renderWithClient(<KnowledgeComponentsPage />)
    await openAssignment('Assignment 487')
    fireEvent.click(await screen.findByRole('button', { name: 'Extrair conceitos' }))

    const dialog = await screen.findByRole('dialog', { name: 'Extraindo conceitos' })
    const current = await within(dialog).findByText(
      'Agrupando os conceitos parecidos e nomeando cada grupo',
    )
    expect(current.closest('li')).toHaveAttribute('aria-current', 'step')
    expect(current.closest('li')).toHaveTextContent('3 de 8')
    expect(within(dialog).queryByRole('button')).not.toBeInTheDocument()

    const cancel = new Event('cancel', { cancelable: true })
    fireEvent(dialog, cancel)
    expect(cancel.defaultPrevented).toBe(true)
    const leaving = new Event('beforeunload', { cancelable: true })
    window.dispatchEvent(leaving)
    expect(leaving.defaultPrevented).toBe(true)
  })

  it('shows the result when the job is done and opens the draft to review', async () => {
    fakeApi({
      job: {
        job_id: 7,
        status: 'done',
        stage: 'qmatrix',
        error_message: null,
        progress_done: null,
        progress_total: null,
      },
    })
    renderWithClient(<KnowledgeComponentsPage />)
    await openAssignment('Assignment 487')
    fireEvent.click(await screen.findByRole('button', { name: 'Extrair conceitos' }))

    const dialog = await screen.findByRole('dialog', { name: 'Conceitos extraídos' })
    expect(await within(dialog).findByText('problemas cobertos')).toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Revisar conceitos' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(
      await screen.findByRole('button', { name: 'Tirar Laços do problema 17' }),
    ).toBeInTheDocument()
  })

  it('shows the technical detail of a failed job and tries again', async () => {
    const spy = fakeApi({
      job: {
        job_id: 7,
        status: 'failed',
        stage: 'generate',
        error_message: 'claude timeout após 120s',
        progress_done: null,
        progress_total: null,
      },
    })
    renderWithClient(<KnowledgeComponentsPage />)
    await openAssignment('Assignment 487')
    fireEvent.click(await screen.findByRole('button', { name: 'Extrair conceitos' }))

    const dialog = await screen.findByRole('dialog', { name: 'A extração não terminou' })
    expect(within(dialog).getByText('claude timeout após 120s')).toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Tentar de novo' }))
    await waitFor(() =>
      expect(calls(spy, 'POST', '/knowledge-components/generation-jobs')).toHaveLength(2),
    )
  })

  it('shows why the start was refused', async () => {
    fakeApi({ refuseStart: true })
    renderWithClient(<KnowledgeComponentsPage />)
    await openAssignment('Assignment 487')
    fireEvent.click(await screen.findByRole('button', { name: 'Extrair conceitos' }))
    const dialog = await screen.findByRole('dialog', {
      name: 'Não foi possível começar a extração',
    })
    expect(within(dialog).getByText('já existe um job em andamento')).toBeInTheDocument()
  })
})

describe('KnowledgeComponentsPage, editing a draft', () => {
  async function openDraft() {
    const spy = fakeApi()
    renderWithClient(<KnowledgeComponentsPage />)
    await openAssignment('Assignment 439')
    await screen.findByRole('button', { name: 'Tirar Laços do problema 5' })
    return spy
  }

  it('takes a concept off a problem right away when nothing is lost', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Tirar Laços do problema 5' }))
    await waitFor(() =>
      expect(calls(spy, 'DELETE', '/knowledge-components/1/problems/5')).toHaveLength(1),
    )
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })

  it('refuses to leave a problem without concepts, without calling the api', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Tirar Laços do problema 12' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Não dá para tirar este conceito' })
    expect(dialog).toHaveTextContent('O problema 12 ficaria sem nenhum conceito')
    expect(calls(spy, 'DELETE', '/knowledge-components/1/problems/12')).toHaveLength(0)
  })

  it('confirms before taking a concept off its last problem', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Tirar Recursão do problema 20' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Tirar Recursão do problema 20?' })
    expect(dialog).toHaveTextContent('sai do exercício junto')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Tirar conceito' }))
    await waitFor(() =>
      expect(calls(spy, 'DELETE', '/knowledge-components/3/problems/20')).toHaveLength(1),
    )
  })

  it('adds an existing concept found by the search', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar conceito ao problema 12' }))
    const dialog = screen.getByRole('dialog', { name: 'Adicionar conceito' })
    expect(within(dialog).queryByRole('radio', { name: /Laços/ })).not.toBeInTheDocument()
    fireEvent.change(within(dialog).getByLabelText(/Buscar um conceito/), {
      target: { value: 'rec' },
    })
    fireEvent.click(within(dialog).getByRole('radio', { name: /Recursão/ }))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Adicionar' }))
    await waitFor(() =>
      expect(calls(spy, 'POST', '/knowledge-components/3/problems/12')).toHaveLength(1),
    )
  })

  it('creates a new concept with the typed name', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Adicionar conceito ao problema 12' }))
    const dialog = screen.getByRole('dialog', { name: 'Adicionar conceito' })
    fireEvent.change(within(dialog).getByLabelText(/Buscar um conceito/), {
      target: { value: 'Vetores' },
    })
    fireEvent.click(within(dialog).getByRole('radio', { name: /Criar “Vetores”/ }))
    fireEvent.click(within(dialog).getByRole('button', { name: 'Adicionar' }))
    await waitFor(() => expect(calls(spy, 'POST', '/knowledge-components')).toHaveLength(1))
    const [, init] = calls(spy, 'POST', '/knowledge-components')[0]
    expect(JSON.parse(String(init!.body))).toEqual({
      assignment_id: 1,
      name: 'Vetores',
      problem_ids: [12],
    })
  })

  it('renames a concept, saying which problems it marks', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Editar o nome de Laços' }))
    const dialog = screen.getByRole('dialog', { name: 'Editar conceito' })
    expect(dialog).toHaveTextContent('Este conceito marca 2 problemas: 5 e 12.')
    fireEvent.change(within(dialog).getByLabelText(/Nome/), { target: { value: 'Repetição' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salvar' }))
    await waitFor(() => expect(calls(spy, 'PUT', '/knowledge-components/1')).toHaveLength(1))
  })

  it('refuses to remove a concept that is the only one of a problem', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Remover Laços do exercício' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Não dá para remover este conceito' })
    expect(dialog).toHaveTextContent('O problema 12 ficaria sem nenhum conceito')
    expect(calls(spy, 'DELETE', '/knowledge-components/1')).toHaveLength(0)
  })

  it('removes a concept after confirming', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Remover Condicionais do exercício' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Remover Condicionais?' })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Remover conceito' }))
    await waitFor(() => expect(calls(spy, 'DELETE', '/knowledge-components/2')).toHaveLength(1))
  })

  it('merges two concepts, previewing the problems that stay', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Mesclar Recursão com outro conceito' }))
    const dialog = screen.getByRole('dialog', { name: 'Mesclar conceitos' })
    fireEvent.change(within(dialog).getByLabelText('Mesclar com'), { target: { value: '2' } })
    fireEvent.click(within(dialog).getByRole('radio', { name: /Manter Condicionais/ }))
    expect(dialog).toHaveTextContent('No fim serão 2 problemas: 5 e 20.')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Mesclar' }))
    await waitFor(() => expect(calls(spy, 'POST', '/knowledge-components/merge')).toHaveLength(1))
    const [, init] = calls(spy, 'POST', '/knowledge-components/merge')[0]
    expect(JSON.parse(String(init!.body))).toEqual({
      assignment_id: 1,
      keep_kc_id: 2,
      drop_kc_id: 3,
    })
  })

  it('approves this exercise only', async () => {
    const spy = await openDraft()
    expect(screen.getByText(/1 de 4 exercícios aprovados/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Aprovar este exercício' }))
    expect(await screen.findByRole('button', { name: 'Exercício aprovado' })).toBeDisabled()
    expect(calls(spy, 'POST', '/knowledge-components/approve')).toHaveLength(1)
    expect(
      await screen.findByText(/Conceitos aprovados. Mexer em qualquer conceito/),
    ).toBeInTheDocument()
  })
})
