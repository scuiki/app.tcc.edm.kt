import { act, fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, renderWithClient } from '../../../test/renderWithClient'
import type { AssignmentStatus, AssignmentSummary } from '../../assignments/api/useAssignments'
import type { ClassroomSummary } from '../../classrooms/api/classrooms'
import type {
  AssignmentProblems,
  GenerationJob,
  KnowledgeComponentOrigin,
  ProblemKnowledgeComponents,
} from '../api/knowledgeComponents'
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

const LOOPS = { id: 1, name: 'Laços', is_generated_by_llm: true }
const IFS = { id: 2, name: 'Condicionais', is_generated_by_llm: true }
// A Recursão foi criada pelo professor, e o nome dela não leva as estrelas
const RECURSION = { id: 3, name: 'Recursão', is_generated_by_llm: false }
const EXTRACTED_AT = '2026-10-07T12:00:00+00:00'
const STATEMENT = 'Escreva um método que devolve a soma de dois inteiros.'
const REOPEN_NOTICE = 'Editar a matriz agora reabre todos os conceitos para aprovação.'

// O problema 12 só tem Laços, a Recursão só marca o problema 20, e só o 5 tem enunciado
function draftProblems(): ProblemKnowledgeComponents[] {
  return [
    {
      problem_id: 5,
      statement: STATEMENT,
      correct_run_count: 12,
      knowledge_components: [LOOPS, IFS],
    },
    {
      problem_id: 12,
      statement: null,
      correct_run_count: 9,
      knowledge_components: [LOOPS],
    },
    {
      problem_id: 20,
      statement: null,
      correct_run_count: 7,
      knowledge_components: [IFS, RECURSION],
    },
  ]
}

// O código como o banco guarda, com o fim de linha do Windows e a tabulação
const SUM = 'int sum(int a, int b) {\r\n\treturn a + b;\r\n}\r\n'
const LOOP_SUM =
  'int sum(int[] values) {\r\n\tint total = 0;\r\n\tfor (int v : values) {\r\n\t\ttotal += v;\r\n\t}\r\n\treturn total;\r\n}\r\n'
const LOOP_REASONING = 'Toda solução percorre os valores com um laço for, como nas soluções 1 e 2.'
const ENGLISH_NAME = 'Loops'
const ENGLISH_REASONING = 'Every solution iterates over the values with a for loop.'
const STUDENT_ATTEMPT = 'Tentativa 7 do aluno 4321'

// A origem de cada conceito do rascunho, que a lupa pede pela rota da origem
function draftOrigins(): Record<number, KnowledgeComponentOrigin> {
  return {
    // O trecho na solução 2 do problema 5, e no 12 o modelo justificou mas o trecho foi descartado
    1: {
      kc_id: 1,
      name: 'Laços',
      is_generated_by_llm: true,
      problems: [
        {
          problem_id: 5,
          statement: STATEMENT,
          translated_reasonings: [LOOP_REASONING],
          evidence: { position: 2, first_line: 3, last_line: 5 },
          sampled_solutions: [
            { position: 1, code: SUM },
            { position: 2, code: LOOP_SUM },
            { position: 3, code: SUM },
          ],
        },
        {
          problem_id: 12,
          statement: null,
          translated_reasonings: [
            'O problema pede repetir a conta até o fim da lista.',
            'Toda solução usa um laço while.',
          ],
          evidence: null,
          sampled_solutions: [
            { position: 1, code: SUM },
            { position: 2, code: LOOP_SUM },
          ],
        },
      ],
    },
    // O professor ligou as Condicionais ao 5, e o 20 não tem acerto nem solução lida
    2: {
      kc_id: 2,
      name: 'Condicionais',
      is_generated_by_llm: true,
      problems: [
        {
          problem_id: 5,
          statement: STATEMENT,
          translated_reasonings: [],
          evidence: null,
          sampled_solutions: [
            { position: 1, code: SUM },
            { position: 2, code: LOOP_SUM },
          ],
        },
        {
          problem_id: 20,
          statement: null,
          translated_reasonings: [],
          evidence: null,
          sampled_solutions: [],
        },
      ],
    },
    3: {
      kc_id: 3,
      name: 'Recursão',
      is_generated_by_llm: false,
      problems: [
        {
          problem_id: 20,
          statement: null,
          translated_reasonings: [],
          evidence: null,
          sampled_solutions: [],
        },
      ],
    },
  }
}

interface FakeApiOptions {
  classrooms?: ClassroomSummary[]
  job?: GenerationJob
  refuseStart?: boolean
  // Os problemas, a data da extração e a situação do rascunho, o exercício 1
  draft?: ProblemKnowledgeComponents[]
  draftExtractedAt?: string | null
  draftStatus?: AssignmentStatus
  refuseApprove?: boolean
  // A rota da tela fica sem resposta, como uma carga que ainda não voltou
  problemsPending?: boolean
  // Ligar e desligar só respondem quando a promessa resolve, como um pedido ainda a caminho
  linkGate?: Promise<void>
  refuseLink?: boolean
  // A rota da origem falha até a promessa resolver, como a api fora do ar que volta
  originOutage?: Promise<void>
  // A rota da origem fica sem resposta, como uma carga que ainda não voltou
  originPending?: boolean
}

// Uma api em memória, com os exercícios de uma turma e os conceitos de cada um
function fakeApi({
  classrooms = [CLASSROOM],
  job,
  refuseStart = false,
  draft = draftProblems(),
  draftExtractedAt = EXTRACTED_AT,
  draftStatus = 'kc_draft',
  refuseApprove = false,
  problemsPending = false,
  linkGate,
  refuseLink = false,
  originOutage,
  originPending = false,
}: FakeApiOptions = {}) {
  const assignments = [
    assignment(1, 439, draftStatus),
    assignment(2, 487, 'ready_for_kc_generation'),
    assignment(3, 492, 'statistics_only'),
    assignment(4, 502, 'trained'),
  ]
  const problems: Record<number, ProblemKnowledgeComponents[]> = {
    1: draft,
    2: [
      {
        problem_id: 17,
        statement: null,
        correct_run_count: 4,
        knowledge_components: [],
      },
    ],
    3: [],
    4: draftProblems(),
  }
  // Só os exercícios que já passaram pela extração têm a data dela
  const extractedAt: Record<number, string | null> = {
    1: draftExtractedAt,
    2: null,
    3: null,
    4: EXTRACTED_AT,
  }
  const statusOf = (id: number) => assignments.find((a) => a.id === id)!.status
  const origins = draftOrigins()
  let isOriginDown = originOutage != null
  originOutage?.then(() => {
    isOriginDown = false
  })

  const spy = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const path = String(input)
    const method = init?.method ?? 'GET'
    if (refuseLink && method === 'POST' && /\/problems\/\d+$/.test(path)) {
      return jsonResponse({ detail: 'o conceito já marca este problema' }, 409)
    }
    // Toda edição de um conceito devolve o exercício aprovado a rascunho, como o backend faz
    const isEdit =
      method !== 'GET' && /^\/knowledge-components(\/\d+)?(\/problems\/\d+)?$/.test(path)
    if (isEdit && assignments[0].status === 'kc_approved') {
      assignments[0] = { ...assignments[0], status: 'kc_draft' }
    }
    if (path === '/classrooms') return jsonResponse({ classrooms })
    if (path.startsWith('/assignments?classroom_id=')) return jsonResponse({ assignments })
    const problemsMatch = path.match(/^\/assignments\/(\d+)\/problems\/knowledge-components$/)
    if (problemsMatch) {
      if (problemsPending) return new Promise<Response>(() => {})
      const id = Number(problemsMatch[1])
      return jsonResponse({
        assignment_id: id,
        status: statusOf(id),
        extracted_at: extractedAt[id],
        problems: problems[id],
      } satisfies AssignmentProblems)
    }
    const originMatch = path.match(/^\/knowledge-components\/(\d+)\/origin$/)
    if (originMatch && method === 'GET') {
      if (originPending) return new Promise<Response>(() => {})
      if (isOriginDown) return jsonResponse({ detail: 'erro interno' }, 500)
      // Inglês e tentativa estão fora do contrato, e a tela não pode mostrá-los se vierem
      const origin = origins[Number(originMatch[1])]
      return jsonResponse({
        ...origin,
        generated_name: ENGLISH_NAME,
        problems: origin.problems.map((problem) => ({
          ...problem,
          reasonings: [ENGLISH_REASONING],
          sampled_solutions: problem.sampled_solutions.map((solution) => ({
            ...solution,
            attempt: STUDENT_ATTEMPT,
          })),
        })),
      })
    }
    // Renomear grava o nome do professor, e as estrelas saem
    const renameMatch = path.match(/^\/knowledge-components\/(\d+)$/)
    if (renameMatch && method === 'PUT') {
      const kcId = Number(renameMatch[1])
      const { name } = JSON.parse(String(init!.body)) as { name: string }
      const renamed = { id: kcId, name, is_generated_by_llm: false }
      problems[1] = problems[1].map((p) => ({
        ...p,
        knowledge_components: p.knowledge_components.map((k) => (k.id === kcId ? renamed : k)),
      }))
      origins[kcId] = { ...origins[kcId], name, is_generated_by_llm: false }
      return jsonResponse(renamed)
    }
    if (path === '/knowledge-components/generation-jobs' && method === 'POST') {
      if (refuseStart) return jsonResponse({ detail: 'já existe um job em andamento' }, 409)
      return jsonResponse({ job_id: 7, status: 'pending' }, 202)
    }
    if (path === '/knowledge-components/generation-jobs/7') {
      // Quando o job termina, o exercício 2 ganha conceitos e vira rascunho
      if (job?.status === 'done') {
        assignments[1] = { ...assignments[1], status: 'kc_draft' }
        problems[2] = [{ ...problems[2][0], knowledge_components: [LOOPS] }]
        extractedAt[2] = EXTRACTED_AT
      }
      return jsonResponse(job)
    }
    if (path === '/knowledge-components/approve') {
      if (refuseApprove) return jsonResponse({ detail: 'o problema 31 está sem conceito' }, 409)
      assignments[0] = { ...assignments[0], status: 'kc_approved' }
      return jsonResponse({ assignment_id: 1, status: 'kc_approved' })
    }
    // Ligar e desligar mudam o rascunho, e a recarga seguinte já traz a matriz nova
    const linkMatch = path.match(/^\/knowledge-components\/(\d+)\/problems\/(\d+)$/)
    if (linkMatch && (method === 'POST' || method === 'DELETE')) {
      await linkGate
      const [kcId, problemId] = [Number(linkMatch[1]), Number(linkMatch[2])]
      const kc = problems[1].flatMap((p) => p.knowledge_components).find((k) => k.id === kcId)!
      problems[1] = problems[1].map((p) =>
        p.problem_id !== problemId
          ? p
          : {
              ...p,
              knowledge_components:
                method === 'POST'
                  ? [...p.knowledge_components, kc]
                  : p.knowledge_components.filter((k) => k.id !== kcId),
            },
      )
      return jsonResponse({ kc_id: kcId, problem_id: problemId })
    }
    // O conceito novo é do professor, sem as estrelas, e já entra nos problemas marcados
    if (path === '/knowledge-components' && method === 'POST') {
      const body = JSON.parse(String(init!.body)) as { name: string; problem_ids: number[] }
      const created = { id: 9, name: body.name, is_generated_by_llm: false }
      problems[1] = problems[1].map((p) =>
        body.problem_ids.includes(p.problem_id)
          ? { ...p, knowledge_components: [...p.knowledge_components, created] }
          : p,
      )
      return jsonResponse(created, 201)
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

// Os nomes das linhas da matriz, de cima para baixo, sem o cabeçalho e sem a linha das contagens
function rowNames() {
  const matrix = screen.getByRole('table', { name: 'Conceitos por problema' })
  const rows = within(matrix).getAllByRole('row').slice(1, -1)
  return rows.map((row) => within(row).getAllByRole('cell')[0].textContent)
}

function rowOf(name: string) {
  const matrix = screen.getByRole('table', { name: 'Conceitos por problema' })
  return within(matrix)
    .getAllByRole('row')
    .find((row) => within(row).queryAllByRole('cell')[0]?.textContent === name)!
}

// O número do problema no cabeçalho da matriz, que leva o balão
function problemNumber(problemId: number) {
  const header = screen.getByRole('columnheader', { name: String(problemId) })
  return within(header).getByText(String(problemId))
}

// A linha de fatos é o parágrafo do cabeçalho que começa pela contagem dos problemas
async function factsLine() {
  const heading = await screen.findByRole('heading', { level: 1 })
  const header = heading.closest<HTMLElement>('.page-header')!
  return (await within(header).findByText(/^problemas?$/)).closest('p')
}

describe('KnowledgeComponentsPage, the exercise in the address', () => {
  it('shows the path and the status of the exercise named in the address', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    const path = await screen.findByRole('navigation', { name: 'Caminho' })
    expect(path).toHaveTextContent('Turmas›CSEDM Spring 2019›Assignment 439›Conceitos')
    // A etiqueta saiu do caminho, que só navega, e fica ao lado do título
    expect(path).not.toHaveTextContent('Rascunho de conceitos')
    expect(screen.getByText('Rascunho de conceitos')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'CSEDM Spring 2019' })).toHaveAttribute(
      'href',
      '#/classrooms/1',
    )
  })

  it('says the exercise was not found for an id the classroom does not have', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={99} />)
    expect(await screen.findByText('Exercício não encontrado')).toBeInTheDocument()
  })

  it('says there is nothing to extract from a statistics only exercise', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={3} />)
    expect(await screen.findByText('Não há conceitos para extrair')).toBeInTheDocument()
    // O cabeçalho já diz o que é, então o cartão não repete o título
    expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument()
  })

  it('offers the extraction with the blocks and no card title before the concepts exist', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={2} />)
    const empty = (await screen.findByText('Sem conceitos ainda')).closest('.state--empty')!
    expect(empty.querySelector('.state__icon-box svg')).toHaveClass('lucide-blocks')
    expect(empty.querySelector('.lucide-sparkles')).toBeNull()
    expect(within(empty as HTMLElement).getAllByRole('button')).toHaveLength(1)
    expect(
      within(empty as HTMLElement).getByRole('button', { name: 'Extrair conceitos' }),
    ).toBeVisible()
    expect(screen.queryByRole('heading', { level: 2 })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab')).not.toBeInTheDocument()
  })

  it('shows a trained exercise for reference only, with no edit and no approval', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={4} />)
    const cell = await screen.findByRole('button', { name: 'Laços no problema 5' })
    expect(cell).toBeDisabled()
    expect(cell).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: 'Recursão no problema 5' })).toBeDisabled()
    expect(
      screen.getByText(
        'Exercício treinado. Os conceitos ficam só para consulta, para não divergirem do modelo.',
      ),
    ).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Editar o nome/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /^Remover / })).not.toBeInTheDocument()
    // A coluna das ações fica só com a lupa, que abre a origem também no treinado
    const actions = within(rowOf('Laços')).getAllByRole('button').slice(-1)[0]
    expect(actions).toHaveAccessibleName('Ver a origem de Laços')
    expect(actions.closest('td')).toHaveClass('data-table__actions')
    expect(within(actions.closest('td')!).getAllByRole('button')).toHaveLength(1)
    expect(screen.queryByRole('button', { name: /Aprovar/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Novo conceito' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Problemas' }))
    const problemsTable = screen.getByRole('table', { name: 'Problemas' })
    expect(within(problemsTable).queryByRole('button')).not.toBeInTheDocument()
    // A frase de consulta vale nas duas abas
    expect(
      screen.getByText(/Exercício treinado. Os conceitos ficam só para consulta/),
    ).toBeVisible()
  })
})

describe('KnowledgeComponentsPage, the header', () => {
  it('titles the page with the exercise and lists the facts of the draft', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    expect(
      await screen.findByRole('heading', { level: 1, name: 'Assignment 439' }),
    ).toBeInTheDocument()
    expect((await factsLine())?.textContent).toBe(
      '3 problemas, 3 conceitos, extraídos em 07/10/2026, nenhum problema sem conceito',
    )
  })

  it('counts the problems without concept as an alert', async () => {
    fakeApi({
      draft: [
        ...draftProblems(),
        { problem_id: 31, statement: null, correct_run_count: 0, knowledge_components: [] },
      ],
    })
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    const facts = await factsLine()
    expect(facts?.textContent).toBe(
      '4 problemas, 3 conceitos, extraídos em 07/10/2026, 1 problema sem conceito',
    )
    const alert = within(facts!).getByText('problema sem conceito')
    expect(alert.closest('.facts-line__item')).toHaveClass('facts-line__item--alert')
  })

  it('leaves the extraction date out when there is none', async () => {
    fakeApi({ draftExtractedAt: null })
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    expect((await factsLine())?.textContent).toBe(
      '3 problemas, 3 conceitos, nenhum problema sem conceito',
    )
  })

  it('agrees the extraction date with a single concept', async () => {
    fakeApi({
      draft: draftProblems().map((problem) => ({ ...problem, knowledge_components: [LOOPS] })),
    })
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    expect((await factsLine())?.textContent).toBe(
      '3 problemas, 1 conceito, extraído em 07/10/2026, nenhum problema sem conceito',
    )
  })

  it('shows the title and the status before the concepts arrive, without the facts', async () => {
    fakeApi({ problemsPending: true })
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    const heading = await screen.findByRole('heading', { level: 1, name: 'Assignment 439' })
    expect(screen.getByText('Rascunho de conceitos')).toBeInTheDocument()
    expect(screen.getByText('Carregando os conceitos do exercício…')).toBeInTheDocument()
    const header = heading.closest<HTMLElement>('.page-header')!
    expect(header.querySelector('.facts-line')).toBeNull()
  })

  it('shows only the problems before the extraction', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={2} />)
    expect((await factsLine())?.textContent).toBe('1 problema')
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
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={2} />)
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
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={2} />)
    fireEvent.click(await screen.findByRole('button', { name: 'Extrair conceitos' }))

    const dialog = await screen.findByRole('dialog', { name: 'Conceitos extraídos' })
    expect(await within(dialog).findByText('problemas cobertos')).toBeInTheDocument()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Revisar conceitos' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Laços no problema 17' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
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
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={2} />)
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
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={2} />)
    fireEvent.click(await screen.findByRole('button', { name: 'Extrair conceitos' }))
    const dialog = await screen.findByRole('dialog', {
      name: 'Não foi possível começar a extração',
    })
    expect(within(dialog).getByText('já existe um job em andamento')).toBeInTheDocument()
  })
})

describe('KnowledgeComponentsPage, the matrix', () => {
  async function openDraft(options: FakeApiOptions = {}) {
    const spy = fakeApi(options)
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    await screen.findByRole('button', { name: 'Laços no problema 5' })
    return spy
  }

  it('lists the concepts by recurrence, then by name, with the recurrence on the right', async () => {
    await openDraft()
    expect(rowNames()).toEqual(['Condicionais', 'Laços', 'Recursão'])
    expect(within(rowOf('Laços')).getByText('de 3').closest('td')).toHaveTextContent('2 de 3')
    expect(within(rowOf('Recursão')).getByText('de 3').closest('td')).toHaveTextContent('1 de 3')
  })

  it('shows each link as a pressed cell named by the concept and the problem', async () => {
    await openDraft()
    expect(screen.getByRole('button', { name: 'Laços no problema 12' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'Recursão no problema 12' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
    expect(screen.getByRole('button', { name: 'Recursão no problema 12' })).toBeEnabled()
  })

  it('marks the stars only on the names the model gave', async () => {
    await openDraft()
    expect(
      within(rowOf('Laços')).getByRole('img', { name: 'Gerado pelo modelo de linguagem' }),
    ).toBeInTheDocument()
    expect(within(rowOf('Recursão')).queryByRole('img')).not.toBeInTheDocument()
  })

  it('shows the whole name of the concept in the balloon', async () => {
    await openDraft()
    fireEvent.mouseEnter(within(rowOf('Condicionais')).getByText('Condicionais'))
    expect(screen.getByRole('tooltip')).toHaveTextContent('Condicionais')
  })

  it('shows the statement of the problem in the balloon of its number, also by keyboard', async () => {
    await openDraft()
    const number = problemNumber(5)
    expect(number).toHaveAttribute('tabindex', '0')
    act(() => number.focus())
    const tooltip = screen.getByRole('tooltip')
    expect(tooltip.firstElementChild).toHaveTextContent('Problema 5')
    expect(tooltip).toHaveTextContent(STATEMENT)
    act(() => number.blur())

    fireEvent.mouseEnter(problemNumber(12))
    expect(screen.getByRole('tooltip')).toHaveTextContent('Problema 12Sem enunciado.')
  })

  it('counts the concepts of each problem in the last row, the foot of the table', async () => {
    await openDraft()
    const totals = within(screen.getByRole('table', { name: 'Conceitos por problema' }))
      .getAllByRole('row')
      .at(-1)!
    expect(totals.parentElement?.tagName).toBe('TFOOT')
    expect(
      within(totals)
        .getAllByRole('cell')
        .map((cell) => cell.textContent),
    ).toEqual(['Conceitos por problema', '2', '1', '2', '', ''])
  })

  it('marks a problem nobody solved in red, with why it is empty and its statement', async () => {
    await openDraft({
      draft: [
        ...draftProblems(),
        {
          problem_id: 31,
          statement: 'Escreva um método recursivo.',
          correct_run_count: 0,
          knowledge_components: [],
        },
      ],
    })
    const number = problemNumber(31)
    expect(number).toHaveClass('kc-matrix__problem--empty')
    fireEvent.mouseEnter(number)
    const tooltip = screen.getByRole('tooltip')
    expect(tooltip.firstElementChild).toHaveTextContent('Problema 31 sem conceito')
    expect(tooltip).toHaveTextContent(
      'Problema 31 sem conceito' +
        'Ninguém acertou este problema ainda. O modelo de linguagem precisa de execuções corretas para extrair conceitos. Ligue um conceito clicando nas células.' +
        '\n\nEscreva um método recursivo.',
      { normalizeWhitespace: false },
    )

    const totals = within(screen.getByRole('table', { name: 'Conceitos por problema' }))
      .getAllByRole('row')
      .at(-1)!
    const zero = within(totals).getAllByRole('cell')[4]
    expect(zero).toHaveTextContent('0')
    expect(zero.querySelector('.kc-matrix__zero svg')).not.toBeNull()
  })

  it('says only that the problem is empty when it has correct runs and no statement', async () => {
    await openDraft({
      draft: [
        ...draftProblems(),
        { problem_id: 31, statement: null, correct_run_count: 4, knowledge_components: [] },
      ],
    })
    fireEvent.mouseEnter(problemNumber(31))
    expect(screen.getByRole('tooltip')).toHaveTextContent(
      'Problema 31 sem conceito' +
        'Este problema está sem conceito. Ligue um conceito clicando nas células.',
      { normalizeWhitespace: false },
    )
  })

  it('shows the help sentence in the footer of the draft, only on the matrix tab', async () => {
    await openDraft()
    const help = /Clique numa célula para ligar ou desligar o conceito do problema/
    expect(screen.getByText(help)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: 'Problemas' }))
    expect(screen.queryByText(help)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Aprovar conceitos' })).not.toBeInTheDocument()
  })
})

describe('KnowledgeComponentsPage, the problems tab', () => {
  async function openProblems(options: FakeApiOptions = {}) {
    fakeApi(options)
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    fireEvent.click(await screen.findByRole('tab', { name: 'Problemas' }))
    return screen.getByRole('table', { name: 'Problemas' })
  }

  // O texto de cada célula, por linha, sem o cabeçalho
  function bodyOf(table: HTMLElement) {
    return within(table)
      .getAllByRole('row')
      .slice(1)
      .map((row) =>
        within(row)
          .getAllByRole('cell')
          .map((cell) => cell.textContent),
      )
  }

  it('shows a row per problem with only its number, its statement and its concept count', async () => {
    const table = await openProblems()
    expect(
      within(table)
        .getAllByRole('columnheader')
        .map((header) => header.textContent),
    ).toEqual(['Problema', 'Enunciado', 'Conceitos'])
    expect(bodyOf(table)).toEqual([
      ['5', STATEMENT, '2'],
      ['12', 'sem enunciado', '1'],
      ['20', 'sem enunciado', '2'],
    ])
  })

  it('keeps the statement on the left, breaking lines and with no stars', async () => {
    const table = await openProblems()
    const cell = within(table).getByRole('cell', { name: STATEMENT })
    expect(cell).toHaveClass('data-table__wrap', 'data-table__left')
    expect(within(table).getByRole('columnheader', { name: 'Enunciado' })).toHaveClass(
      'data-table__left',
    )
    expect(within(table).queryByRole('img')).not.toBeInTheDocument()
    expect(within(table).getByRole('columnheader', { name: 'Conceitos' })).not.toHaveClass(
      'data-table__left',
    )
  })

  it('says sem enunciado in gray where the package has no statement', async () => {
    const table = await openProblems()
    const missing = within(table).getAllByText('sem enunciado')
    expect(missing).toHaveLength(2)
    missing.forEach((text) => expect(text).toHaveClass('data-table__missing'))
    expect(within(table).queryByText(STATEMENT)).not.toHaveClass('data-table__missing')
  })

  it('shows the 0 of a problem without concepts in red with the alert icon, and no other', async () => {
    const table = await openProblems({
      draft: [
        ...draftProblems(),
        { problem_id: 31, statement: null, correct_run_count: 0, knowledge_components: [] },
      ],
    })
    expect(bodyOf(table).at(-1)).toEqual(['31', 'sem enunciado', '0'])
    const rows = within(table).getAllByRole('row')
    const zero = within(rows.at(-1)!).getAllByRole('cell')[2]
    expect(zero.querySelector('.problem-statements__zero svg')).not.toBeNull()
    rows.slice(1, -1).forEach((row) => expect(row.querySelector('svg')).toBeNull())
  })

  it('has no button, because the matrix is the only place that edits', async () => {
    const table = await openProblems()
    expect(within(table).queryByRole('button')).not.toBeInTheDocument()
  })
})

describe('KnowledgeComponentsPage, editing a draft', () => {
  async function openDraft() {
    const spy = fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    await screen.findByRole('button', { name: 'Laços no problema 5' })
    return spy
  }

  it('links a concept by clicking an empty cell', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 5' }))
    await waitFor(() =>
      expect(calls(spy, 'POST', '/knowledge-components/3/problems/5')).toHaveLength(1),
    )
    expect(
      await screen.findByRole('button', { name: 'Recursão no problema 5', pressed: true }),
    ).toBeInTheDocument()
  })

  it('sends a single request for a double click on the same cell', async () => {
    const spy = await openDraft()
    const cell = screen.getByRole('button', { name: 'Recursão no problema 5' })
    act(() => {
      fireEvent.click(cell)
      fireEvent.click(cell)
    })
    expect(
      await screen.findByRole('button', { name: 'Recursão no problema 5', pressed: true }),
    ).toBeEnabled()
    expect(calls(spy, 'POST', '/knowledge-components/3/problems/5')).toHaveLength(1)
  })

  it('does not hold the other cells while one request is on the way', async () => {
    const spy = await openDraft()
    act(() => {
      fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 5' }))
      fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 12' }))
    })
    await waitFor(() => {
      expect(calls(spy, 'POST', '/knowledge-components/3/problems/5')).toHaveLength(1)
      expect(calls(spy, 'POST', '/knowledge-components/3/problems/12')).toHaveLength(1)
    })
  })

  it('takes a concept off a problem right away when nothing is lost', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Laços no problema 5' }))
    await waitFor(() =>
      expect(calls(spy, 'DELETE', '/knowledge-components/1/problems/5')).toHaveLength(1),
    )
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })

  it('keeps every row in place after linking and unlinking', async () => {
    await openDraft()
    // Sem a ordem fixa, Condicionais desceria ao marcar um problema só, e a Recursão subiria
    fireEvent.click(screen.getByRole('button', { name: 'Condicionais no problema 5' }))
    expect(
      await screen.findByRole('button', { name: 'Condicionais no problema 5', pressed: false }),
    ).toBeInTheDocument()
    expect(rowNames()).toEqual(['Condicionais', 'Laços', 'Recursão'])

    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 5' }))
    expect(
      await screen.findByRole('button', { name: 'Recursão no problema 5', pressed: true }),
    ).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 12' }))
    expect(
      await screen.findByRole('button', { name: 'Recursão no problema 12', pressed: true }),
    ).toBeInTheDocument()
    expect(within(rowOf('Recursão')).getByText('de 3').closest('td')).toHaveTextContent('3 de 3')
    expect(rowNames()).toEqual(['Condicionais', 'Laços', 'Recursão'])
  })

  it('refuses to leave a problem without concepts, without calling the api', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Laços no problema 12' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Não dá para tirar este conceito' })
    expect(dialog).toHaveTextContent('O problema 12 ficaria sem nenhum conceito')
    expect(calls(spy, 'DELETE', '/knowledge-components/1/problems/12')).toHaveLength(0)
  })

  it('confirms before taking a concept off its last problem', async () => {
    const spy = await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 20' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Tirar Recursão do problema 20?' })
    expect(dialog).toHaveTextContent('sai do exercício junto')
    fireEvent.click(within(dialog).getByRole('button', { name: 'Tirar conceito' }))
    await waitFor(() =>
      expect(calls(spy, 'DELETE', '/knowledge-components/3/problems/20')).toHaveLength(1),
    )
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

  it('warns that the stars leave when renaming a name the model gave', async () => {
    await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Editar o nome de Laços' }))
    expect(screen.getByRole('dialog', { name: 'Editar conceito' })).toHaveTextContent(
      'O nome atual veio do modelo de linguagem. Ao salvar, o nome passa a ser seu e as estrelas saem.',
    )
  })

  it('says nothing about the stars when renaming a concept the teacher created', async () => {
    await openDraft()
    fireEvent.click(screen.getByRole('button', { name: 'Editar o nome de Recursão' }))
    const dialog = screen.getByRole('dialog', { name: 'Editar conceito' })
    expect(dialog).toHaveTextContent('Este conceito marca 1 problema: 20.')
    expect(dialog).not.toHaveTextContent(/estrelas/)
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

  it('says nothing about reopening the approval in a draft', async () => {
    const spy = await openDraft()
    const dialogs = [
      () => fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 20' })),
      () =>
        fireEvent.click(screen.getByRole('button', { name: 'Remover Condicionais do exercício' })),
      () => fireEvent.click(screen.getByRole('button', { name: 'Editar o nome de Laços' })),
      () => fireEvent.click(screen.getByRole('button', { name: 'Novo conceito' })),
    ]
    for (const open of dialogs) {
      open()
      const dialog = document.querySelector<HTMLElement>('dialog[open]')!
      expect(dialog).not.toHaveTextContent(REOPEN_NOTICE)
      fireEvent.click(within(dialog).getByRole('button', { name: 'Cancelar' }))
      expect(document.querySelector('dialog[open]')).toBeNull()
    }

    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 5' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await waitFor(() =>
      expect(calls(spy, 'POST', '/knowledge-components/3/problems/5')).toHaveLength(1),
    )
  })
})

describe('KnowledgeComponentsPage, editing approved concepts', () => {
  async function openApproved(options: FakeApiOptions = {}) {
    const spy = fakeApi({ ...options, draftStatus: 'kc_approved' })
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    await screen.findByRole('button', { name: 'Laços no problema 5' })
    return spy
  }

  function reopenDialog() {
    return screen.getByRole('dialog', { name: 'Editar os conceitos aprovados?' })
  }

  it('keeps the approval in sight and disabled, with no notice above the card', async () => {
    await openApproved()
    expect(screen.getByRole('button', { name: 'Aprovar conceitos' })).toBeDisabled()
    expect(screen.queryByText(/Mexer em qualquer conceito/)).not.toBeInTheDocument()
    expect(screen.queryByText(REOPEN_NOTICE)).not.toBeInTheDocument()
  })

  it('warns before linking a cell, in a neutral dialog, and cancelling calls nothing', async () => {
    const spy = await openApproved()
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 5' }))
    const dialog = reopenDialog()
    expect(dialog).toHaveTextContent(
      `${REOPEN_NOTICE}O exercício volta a rascunho, e você aprova de novo quando terminar.`,
    )
    // O primeiro focável do aviso é o Cancelar, e o foco nele não abre balão
    const cancel = within(dialog).getAllByRole('button')[0]
    act(() => cancel.focus())
    expect(cancel).toHaveTextContent('Cancelar')
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    const follow = within(dialog).getByRole('button', { name: 'Ligar conceito' })
    expect(follow).toHaveClass('btn--primary')
    expect(
      within(dialog)
        .getAllByRole('button')
        .map((button) => button.textContent),
    ).toEqual(['Cancelar', 'Ligar conceito'])

    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(spy.mock.calls.filter(([, init]) => (init?.method ?? 'GET') !== 'GET')).toHaveLength(0)
    expect(screen.getByRole('button', { name: 'Recursão no problema 5' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )
  })

  it('links after the warning, and the reload brings back the draft and the approval', async () => {
    const spy = await openApproved()
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 5' }))
    fireEvent.click(within(reopenDialog()).getByRole('button', { name: 'Ligar conceito' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(calls(spy, 'POST', '/knowledge-components/3/problems/5')).toHaveLength(1)
    expect(
      await screen.findByRole('button', { name: 'Recursão no problema 5', pressed: true }),
    ).toBeInTheDocument()
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Aprovar conceitos' })).toBeEnabled(),
    )

    // Sem estado de já avisei, a recarga trouxe o rascunho e o clique seguinte liga direto
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 12' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    await waitFor(() =>
      expect(calls(spy, 'POST', '/knowledge-components/3/problems/12')).toHaveLength(1),
    )
  })

  it('warns before unlinking a cell, and following sends the DELETE', async () => {
    const spy = await openApproved()
    fireEvent.click(screen.getByRole('button', { name: 'Laços no problema 5' }))
    const follow = within(reopenDialog()).getByRole('button', { name: 'Tirar conceito' })
    expect(follow).toHaveClass('btn--primary')
    expect(calls(spy, 'DELETE', '/knowledge-components/1/problems/5')).toHaveLength(0)
    fireEvent.click(follow)
    await waitFor(() =>
      expect(calls(spy, 'DELETE', '/knowledge-components/1/problems/5')).toHaveLength(1),
    )
    expect(
      await screen.findByRole('button', { name: 'Laços no problema 5', pressed: false }),
    ).toBeInTheDocument()
  })

  it('keeps the warning open and without clicks while the request is on the way', async () => {
    let release!: () => void
    const linkGate = new Promise<void>((resolve) => {
      release = resolve
    })
    const spy = await openApproved({ linkGate })
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 5' }))
    fireEvent.click(within(reopenDialog()).getByRole('button', { name: 'Ligar conceito' }))
    await waitFor(() =>
      expect(calls(spy, 'POST', '/knowledge-components/3/problems/5')).toHaveLength(1),
    )
    const buttons = within(reopenDialog()).getAllByRole('button')
    expect(buttons.map((button) => button.textContent)).toEqual(['Cancelar', 'Ligar conceito'])
    buttons.forEach((button) => expect(button).toBeDisabled())
    // Com o pedido no ar o Esc não larga o aviso
    const cancel = new Event('cancel', { cancelable: true })
    fireEvent(reopenDialog(), cancel)
    expect(cancel.defaultPrevented).toBe(true)

    act(() => release())
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'Recursão no problema 5' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('closes the warning and shows the error in the card when the request fails', async () => {
    await openApproved({ refuseLink: true })
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 5' }))
    fireEvent.click(within(reopenDialog()).getByRole('button', { name: 'Ligar conceito' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Não foi possível ligar o conceito')
    expect(alert).toHaveTextContent('A mudança foi recusada. o conceito já marca este problema')
    expect(alert.closest('.card')).not.toBeNull()
  })

  it('sends a single request for a double click on the follow button', async () => {
    const spy = await openApproved()
    const cell = screen.getByRole('button', { name: 'Recursão no problema 5' })
    fireEvent.click(cell)
    const follow = within(reopenDialog()).getByRole('button', { name: 'Ligar conceito' })
    act(() => {
      fireEvent.click(follow)
      fireEvent.click(follow)
      // Com o pedido no ar, um clique na mesma célula não troca o aviso que está enviando
      fireEvent.click(cell)
    })
    expect(within(reopenDialog()).getByRole('button', { name: 'Ligar conceito' })).toBeDisabled()
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(
      screen.getByRole('button', { name: 'Recursão no problema 5', pressed: true }),
    ).toBeEnabled()
    expect(calls(spy, 'POST', '/knowledge-components/3/problems/5')).toHaveLength(1)
  })

  it('refuses to leave a problem empty with no warning, because nothing changes', async () => {
    await openApproved()
    fireEvent.click(screen.getByRole('button', { name: 'Laços no problema 12' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Não dá para tirar este conceito' })
    expect(dialog).not.toHaveTextContent(REOPEN_NOTICE)
    expect(
      screen.queryByRole('dialog', { name: 'Editar os conceitos aprovados?' }),
    ).not.toBeInTheDocument()
  })

  it('puts the warning as a line in the confirmation of taking off the last problem', async () => {
    const spy = await openApproved()
    fireEvent.click(screen.getByRole('button', { name: 'Recursão no problema 20' }))
    expect(
      screen.queryByRole('dialog', { name: 'Editar os conceitos aprovados?' }),
    ).not.toBeInTheDocument()
    const dialog = screen.getByRole('alertdialog', { name: 'Tirar Recursão do problema 20?' })
    const line = within(dialog).getByText(REOPEN_NOTICE)
    expect(line).toHaveClass('kc-dialog__note')
    expect(line.parentElement?.lastElementChild).toBe(line)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Tirar conceito' }))
    await waitFor(() =>
      expect(calls(spy, 'DELETE', '/knowledge-components/3/problems/20')).toHaveLength(1),
    )
  })

  it('puts the warning as a line in the confirmation of removing, not in the refusal', async () => {
    await openApproved()
    fireEvent.click(screen.getByRole('button', { name: 'Remover Condicionais do exercício' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Remover Condicionais?' })
    const line = within(dialog).getByText(REOPEN_NOTICE)
    expect(line).toHaveClass('kc-dialog__note')
    expect(line.parentElement?.lastElementChild).toBe(line)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Cancelar' }))

    fireEvent.click(screen.getByRole('button', { name: 'Remover Laços do exercício' }))
    expect(
      screen.getByRole('alertdialog', { name: 'Não dá para remover este conceito' }),
    ).not.toHaveTextContent(REOPEN_NOTICE)
  })

  it('puts the warning as a line above the buttons of the rename form', async () => {
    const spy = await openApproved()
    fireEvent.click(screen.getByRole('button', { name: 'Editar o nome de Laços' }))
    const dialog = screen.getByRole('dialog', { name: 'Editar conceito' })
    const line = within(dialog).getByText(REOPEN_NOTICE)
    expect(line).toHaveClass('kc-dialog__note')
    expect(line.parentElement?.lastElementChild).toBe(line)
    fireEvent.change(within(dialog).getByLabelText(/Nome/), { target: { value: 'Repetição' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salvar' }))
    await waitFor(() => expect(calls(spy, 'PUT', '/knowledge-components/1')).toHaveLength(1))
  })

  it('puts the warning as a line above the buttons of the new concept form', async () => {
    await openApproved()
    fireEvent.click(screen.getByRole('button', { name: 'Novo conceito' }))
    const dialog = screen.getByRole('dialog', { name: 'Novo conceito' })
    const line = within(dialog).getByText(REOPEN_NOTICE)
    expect(line).toHaveClass('kc-dialog__note')
    expect(line.parentElement?.lastElementChild).toBe(line)
  })
})

describe('KnowledgeComponentsPage, a new concept', () => {
  async function openNewConcept(options: FakeApiOptions = {}) {
    const spy = fakeApi(options)
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    fireEvent.click(await screen.findByRole('button', { name: 'Novo conceito' }))
    const dialog = screen.getByRole('dialog', { name: 'Novo conceito' })
    return {
      spy,
      dialog,
      name: within(dialog).getByRole('textbox', { name: 'Nome' }),
      create: within(dialog).getByRole('button', { name: 'Criar' }),
      problem: (problemId: number) =>
        within(dialog).getByRole('checkbox', { name: String(problemId) }),
    }
  }

  it('sits left of the approval on the matrix tab, and no problem adds a concept anymore', async () => {
    fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    const newConcept = await screen.findByRole('button', { name: 'Novo conceito' })
    expect(newConcept.parentElement).toHaveClass('tabs__actions')
    expect(newConcept.nextElementSibling).toBe(
      screen.getByRole('button', { name: 'Aprovar conceitos' }),
    )
    fireEvent.click(screen.getByRole('tab', { name: 'Problemas' }))
    expect(screen.queryByRole('button', { name: 'Novo conceito' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Adicionar/ })).not.toBeInTheDocument()
  })

  it('opens on the name, with no balloon, and a box per problem with only its number', async () => {
    const { dialog, name, problem } = await openNewConcept({
      draft: [
        ...draftProblems(),
        { problem_id: 31, statement: null, correct_run_count: 0, knowledge_components: [] },
      ],
    })
    expect(name).toHaveFocus()
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    const group = within(dialog).getByRole('group', { name: 'Problemas' })
    const boxes = within(group).getAllByRole('checkbox')
    expect(boxes).toEqual([problem(5), problem(12), problem(20), problem(31)])
    boxes.forEach((box) => expect(box).not.toBeChecked())
    expect(problem(5)).toHaveAccessibleDescription(`${STATEMENT} 2 conceitos`)
    expect(problem(12)).toHaveAccessibleDescription('sem enunciado 1 conceito')
    expect(problem(31)).toHaveAccessibleDescription('sem enunciado sem conceito')
    const empty = within(group).getByText('sem conceito')
    expect(empty).toHaveClass('kc-new__count--empty')
    expect(empty.querySelector('svg')).not.toBeNull()
  })

  it('enables Criar only with a name and at least one problem', async () => {
    const { name, create, problem } = await openNewConcept()
    expect(create).toBeDisabled()
    fireEvent.change(name, { target: { value: 'Vetores' } })
    expect(create).toBeDisabled()
    fireEvent.click(problem(12))
    expect(create).toBeEnabled()
    fireEvent.change(name, { target: { value: '   ' } })
    expect(create).toBeDisabled()
    fireEvent.change(name, { target: { value: 'Vetores' } })
    fireEvent.click(problem(12))
    expect(create).toBeDisabled()
  })

  it('refuses a name that already exists in the field, ignoring accents and case', async () => {
    const { spy, name, create, problem } = await openNewConcept()
    fireEvent.click(problem(12))
    fireEvent.change(name, { target: { value: '  lacos ' } })
    expect(name).toHaveAttribute('aria-invalid', 'true')
    expect(name).toHaveAccessibleDescription('Já existe um conceito com este nome.')
    expect(create).toBeDisabled()
    fireEvent.submit(name.closest('form')!)
    expect(calls(spy, 'POST', '/knowledge-components')).toHaveLength(0)

    fireEvent.change(name, { target: { value: 'Laços aninhados' } })
    expect(name).not.toHaveAttribute('aria-invalid')
    expect(create).toBeEnabled()
  })

  it('creates the concept on the marked problems and adds it at the end of the matrix', async () => {
    const { spy, name, create, problem } = await openNewConcept()
    fireEvent.change(name, { target: { value: ' Vetores ' } })
    fireEvent.click(problem(20))
    fireEvent.click(problem(12))
    fireEvent.click(create)
    await waitFor(() => expect(calls(spy, 'POST', '/knowledge-components')).toHaveLength(1))
    const [, init] = calls(spy, 'POST', '/knowledge-components')[0]
    expect(JSON.parse(String(init!.body))).toEqual({
      assignment_id: 1,
      name: 'Vetores',
      problem_ids: [12, 20],
    })
    expect(
      await screen.findByRole('button', { name: 'Vetores no problema 20', pressed: true }),
    ).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    // Pela recorrência a Vetores subiria acima da Recursão, e a ordem fixa a põe no fim
    expect(rowNames()).toEqual(['Condicionais', 'Laços', 'Recursão', 'Vetores'])
    expect(within(rowOf('Vetores')).queryByRole('img')).not.toBeInTheDocument()
  })

  it('says the new concept is born without stars', async () => {
    const { dialog } = await openNewConcept()
    expect(dialog).toHaveTextContent('O conceito novo nasce sem estrelas, porque o nome é seu.')
  })
})

describe('KnowledgeComponentsPage, approving', () => {
  it('approves the draft and disables the button, with no notice above the card', async () => {
    const spy = fakeApi()
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    const approve = await screen.findByRole('button', { name: 'Aprovar conceitos' })
    expect(approve).toBeEnabled()
    fireEvent.click(approve)
    await waitFor(() => expect(calls(spy, 'POST', '/knowledge-components/approve')).toHaveLength(1))
    // A etiqueta ao lado do título é o único lugar que diz que os conceitos estão aprovados
    expect(await screen.findByText('Conceitos aprovados')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Aprovar conceitos' })).toBeDisabled()
    expect(screen.queryByText(/Mexer em qualquer conceito/)).not.toBeInTheDocument()
  })

  it('disables the approval while a problem has no concept, with no reason attached', async () => {
    const spy = fakeApi({
      draft: [
        ...draftProblems(),
        { problem_id: 31, statement: null, correct_run_count: 0, knowledge_components: [] },
      ],
    })
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    const approve = await screen.findByRole('button', { name: 'Aprovar conceitos' })
    expect(approve).toBeDisabled()
    expect(approve).not.toHaveAttribute('title')
    expect(approve).not.toHaveAttribute('aria-describedby')
    // O botão mora direto nas ações das abas, sem o invólucro de um balão em volta
    expect(approve.parentElement).toHaveClass('tabs__actions')
    fireEvent.click(approve)
    expect(calls(spy, 'POST', '/knowledge-components/approve')).toHaveLength(0)
  })

  it('keeps the approved matrix editable, with the approval disabled and no footer sentence', async () => {
    fakeApi({ draftStatus: 'kc_approved' })
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    expect(await screen.findByRole('button', { name: 'Aprovar conceitos' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Laços no problema 5' })).toBeEnabled()
    expect(screen.getByRole('button', { name: 'Editar o nome de Laços' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Novo conceito' })).toBeEnabled()
    expect(screen.queryByText(/Mexer em qualquer conceito/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Clique numa célula/)).not.toBeInTheDocument()
  })

  it('shows why the approval was refused inside the card', async () => {
    fakeApi({ refuseApprove: true })
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={1} />)
    fireEvent.click(await screen.findByRole('button', { name: 'Aprovar conceitos' }))
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent('Não foi possível aprovar os conceitos')
    expect(alert).toHaveTextContent('A mudança foi recusada. o problema 31 está sem conceito')
    expect(alert.closest('.card')).toContainElement(
      screen.getByRole('table', { name: 'Conceitos por problema' }),
    )
  })
})

describe('KnowledgeComponentsPage, the origin of a concept', () => {
  async function openOrigin(name: string, options: FakeApiOptions = {}, assignmentId = 1) {
    const spy = fakeApi(options)
    renderWithClient(<KnowledgeComponentsPage classroomId={1} assignmentId={assignmentId} />)
    fireEvent.click(await screen.findByRole('button', { name: `Ver a origem de ${name}` }))
    const dialog = await screen.findByRole('dialog', { name })
    return { spy, dialog }
  }

  // O painel do problema aberto, depois que a rota da origem responde
  async function panelOf(dialog: HTMLElement, problemId: number) {
    return within(dialog).findByRole('tabpanel', { name: `Problema ${problemId}` })
  }

  function problemTab(dialog: HTMLElement, problemId: number) {
    const problems = within(dialog).getByRole('tablist', {
      name: 'Problemas em que o conceito aparece',
    })
    return within(problems).getByRole('tab', { name: `Problema ${problemId}` })
  }

  it('asks the origin route from the magnifier, in the wide dialog titled by the concept', async () => {
    const { spy, dialog } = await openOrigin('Laços')
    await panelOf(dialog, 5)
    expect(calls(spy, 'GET', '/knowledge-components/1/origin')).toHaveLength(1)
    expect(dialog).toHaveClass('dialog--wide')
    // As estrelas de 24px ficam ao lado do título, fora do nome do diálogo
    const heading = within(dialog).getByRole('heading', { level: 2, name: 'Laços' })
    const stars = heading.nextElementSibling
    expect(stars).toHaveAccessibleName('Gerado pelo modelo de linguagem')
    expect(stars).toHaveClass('generated-by-llm--title')
    expect(
      within(dialog)
        .getByText(/^aparece em/)
        .closest('p'),
    ).toHaveTextContent('aparece em 2 de 3 problemas')
  })

  it('leaves the stars out of the title of a concept the teacher named', async () => {
    const { dialog } = await openOrigin('Recursão')
    await panelOf(dialog, 20)
    const heading = within(dialog).getByRole('heading', { level: 2, name: 'Recursão' })
    expect(heading.parentElement!.querySelector('.generated-by-llm')).toBeNull()
    expect(
      within(dialog)
        .getByText(/^aparece em/)
        .closest('p'),
    ).toHaveTextContent('aparece em 1 de 3 problemas')
  })

  it('opens from the magnifier of a trained exercise too', async () => {
    const { spy, dialog } = await openOrigin('Laços', {}, 4)
    await panelOf(dialog, 5)
    expect(calls(spy, 'GET', '/knowledge-components/1/origin')).toHaveLength(1)
  })

  it('names each problem tab Problema N, with only the number on it and the label once', async () => {
    const { dialog } = await openOrigin('Laços')
    await panelOf(dialog, 5)
    const problems = within(dialog).getByRole('tablist', {
      name: 'Problemas em que o conceito aparece',
    })
    const tabs = within(problems).getAllByRole('tab')
    expect(tabs.map((tab) => tab.textContent)).toEqual(['5', '12'])
    expect(tabs[0]).toHaveAccessibleName('Problema 5')
    expect(tabs[1]).toHaveAccessibleName('Problema 12')
    expect(tabs[0]).toHaveAttribute('aria-selected', 'true')
    const label = within(dialog).getByText('Problema', { exact: true })
    expect(label).toHaveAttribute('aria-hidden', 'true')
    expect(problems).not.toContainElement(label)
  })

  it('shows the statement of the problem, and sem enunciado without one', async () => {
    const { dialog } = await openOrigin('Laços')
    const first = await panelOf(dialog, 5)
    expect(within(first).getByRole('heading', { name: 'Enunciado do problema 5' })).toBeVisible()
    expect(within(first).getByText(STATEMENT)).toBeInTheDocument()

    fireEvent.click(problemTab(dialog, 12))
    const second = await panelOf(dialog, 12)
    expect(within(second).getByRole('heading', { name: 'Enunciado do problema 12' })).toBeVisible()
    expect(within(second).getByText('sem enunciado')).toHaveClass('kc-origin__no-statement')
  })

  it('shows the reasoning under its label, with the stars before it and the hint after', async () => {
    const { dialog } = await openOrigin('Laços')
    const panel = await panelOf(dialog, 5)
    const label = within(panel).getByRole('heading', {
      name: 'Justificativa do modelo de linguagem',
    })
    expect(label.previousElementSibling).toHaveAccessibleName('Gerado pelo modelo de linguagem')
    expect(label.previousElementSibling).toHaveClass('generated-by-llm--label')
    const hint = label.nextElementSibling as HTMLElement
    expect(hint).toHaveAccessibleName(
      'A frase em que o modelo de linguagem explica por que o problema exige o conceito, traduzida. Os números citados são os das abas das soluções.',
    )
    expect(within(panel).getByText(LOOP_REASONING)).toBeInTheDocument()
    // A ordem dos blocos é enunciado, justificativa e soluções
    expect(
      within(panel)
        .getAllByRole('heading')
        .map((heading) => heading.textContent),
    ).toEqual([
      'Enunciado do problema 5',
      'Justificativa do modelo de linguagem',
      'Soluções que o modelo leu',
    ])
  })

  it('opens the solutions on the one with the evidence, with its lines highlighted', async () => {
    const { dialog } = await openOrigin('Laços')
    const panel = await panelOf(dialog, 5)
    const solutions = within(panel).getByRole('tablist', {
      name: 'Soluções do problema 5 que o modelo leu',
    })
    const tabs = within(solutions).getAllByRole('tab')
    expect(tabs.map((tab) => tab.textContent)).toEqual(['Solução 1', 'Solução 2', 'Solução 3'])
    expect(tabs[1]).toHaveAccessibleName('Solução 2, com o trecho')
    expect(tabs[1]).toHaveAttribute('aria-selected', 'true')
    expect(within(tabs[1]).getByRole('img')).toHaveClass('generated-by-llm--tab')
    expect(within(tabs[0]).queryByRole('img')).not.toBeInTheDocument()
    const code = within(panel).getByRole('tabpanel', { name: 'Solução 2, com o trecho' })
    const highlighted = [...code.querySelectorAll('.code-block__number.is-highlighted')]
    expect(highlighted.map((number) => number.textContent)).toEqual(['3', '4', '5'])
    // A dica das soluções diz onde o modelo aponta o conceito, sem chamar o trecho de justificativa
    const hint = within(panel)
      .getByRole('heading', { name: 'Soluções que o modelo leu' })
      .nextElementSibling!.getAttribute('aria-label')!
    expect(hint).toContain('As linhas destacadas mostram onde o modelo aponta o conceito')
    expect(hint).not.toMatch(/justificativa/i)
  })

  it('says the evidence was discarded and opens on the first solution, with no stars', async () => {
    const { dialog } = await openOrigin('Laços')
    await panelOf(dialog, 5)
    fireEvent.click(problemTab(dialog, 12))
    const panel = await panelOf(dialog, 12)
    expect(
      within(panel).getByText(
        'O modelo apontou um trecho que não está nas soluções, e o app o descartou.',
      ),
    ).toBeInTheDocument()
    // As duas justificativas aparecem, cada uma no seu parágrafo
    expect(within(panel).getByText('Toda solução usa um laço while.')).toBeInTheDocument()
    const solutions = within(panel).getByRole('tablist', {
      name: 'Soluções do problema 12 que o modelo leu',
    })
    expect(within(solutions).getByRole('tab', { name: 'Solução 1' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(within(solutions).queryByRole('img')).not.toBeInTheDocument()
    expect(panel.querySelector('.is-highlighted')).toBeNull()
  })

  it('says the teacher made the link, with no reasoning, no stars and no highlight', async () => {
    const { dialog } = await openOrigin('Condicionais')
    const panel = await panelOf(dialog, 5)
    expect(
      within(panel).getByText(
        'O professor ligou este conceito a este problema. Não há justificativa nem trecho do modelo.',
      ),
    ).toBeInTheDocument()
    const label = within(panel).getByRole('heading', {
      name: 'Justificativa do modelo de linguagem',
    })
    expect(label.parentElement!.querySelector('.generated-by-llm')).toBeNull()
    expect(within(panel).getByRole('tab', { name: 'Solução 1' })).toHaveAttribute(
      'aria-selected',
      'true',
    )
    expect(panel.querySelector('.is-highlighted')).toBeNull()
  })

  it('says nobody solved the problem in place of the code it never read', async () => {
    const { dialog } = await openOrigin('Condicionais')
    await panelOf(dialog, 5)
    fireEvent.click(problemTab(dialog, 20))
    const panel = await panelOf(dialog, 20)
    expect(
      within(panel).getByText(
        'Ninguém acertou este problema, então o modelo não leu nenhuma solução dele.',
      ),
    ).toHaveClass('kc-origin__no-solutions')
    expect(within(panel).queryByRole('tablist')).not.toBeInTheDocument()
    expect(within(panel).getByRole('heading', { name: 'Soluções que o modelo leu' })).toBeVisible()
  })

  it('shows neither the English name, the English reasoning nor the attempt the route carries', async () => {
    const { dialog } = await openOrigin('Laços')
    await panelOf(dialog, 5)
    fireEvent.click(problemTab(dialog, 12))
    await panelOf(dialog, 12)
    expect(dialog).not.toHaveTextContent(ENGLISH_NAME)
    expect(dialog).not.toHaveTextContent(ENGLISH_REASONING)
    expect(dialog).not.toHaveTextContent(STUDENT_ATTEMPT)
    expect(dialog).not.toHaveTextContent(/tentativa/i)
  })

  it('asks the origin again after a rename, with the new name and no stars', async () => {
    const { spy, dialog } = await openOrigin('Laços')
    await panelOf(dialog, 5)
    fireEvent.click(within(dialog).getByRole('button', { name: 'Fechar' }))

    fireEvent.click(screen.getByRole('button', { name: 'Editar o nome de Laços' }))
    const rename = screen.getByRole('dialog', { name: 'Editar conceito' })
    fireEvent.change(within(rename).getByLabelText(/Nome/), { target: { value: 'Repetição' } })
    fireEvent.click(within(rename).getByRole('button', { name: 'Salvar' }))
    await waitFor(() => expect(calls(spy, 'PUT', '/knowledge-components/1')).toHaveLength(1))

    fireEvent.click(await screen.findByRole('button', { name: 'Ver a origem de Repetição' }))
    const reopened = screen.getByRole('dialog', { name: 'Repetição' })
    // Sem a resposta de antes da edição no cache, a origem reabre carregando
    expect(within(reopened).getByRole('status')).toHaveTextContent(
      'Carregando a origem do conceito…',
    )
    await panelOf(reopened, 5)
    expect(calls(spy, 'GET', '/knowledge-components/1/origin')).toHaveLength(2)
    const heading = within(reopened).getByRole('heading', { level: 2, name: 'Repetição' })
    expect(heading.parentElement!.querySelector('.generated-by-llm')).toBeNull()
  })

  it('opens without a balloon, and closes from the footer', async () => {
    const { dialog } = await openOrigin('Laços')
    await panelOf(dialog, 5)
    expect(screen.queryByRole('tooltip')).not.toBeInTheDocument()
    const footer = within(dialog).getByRole('button', { name: 'Fechar' })
    expect(footer.closest('.dialog__footer')).not.toBeNull()
    fireEvent.click(footer)
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('says it is loading under the header that the screen already knows', async () => {
    const { dialog } = await openOrigin('Laços', { originPending: true })
    expect(within(dialog).getByRole('status')).toHaveTextContent('Carregando a origem do conceito…')
    expect(within(dialog).getByRole('heading', { level: 2, name: 'Laços' })).toBeVisible()
    expect(within(dialog).getByText(/^aparece em/)).toBeInTheDocument()
    expect(within(dialog).queryByRole('tablist')).not.toBeInTheDocument()
  })

  it('shows the error with a retry that asks the route again', async () => {
    let restore = () => {}
    const outage = new Promise<void>((resolve) => {
      restore = resolve
    })
    const { spy, dialog } = await openOrigin('Laços', { originOutage: outage })
    const alert = await within(dialog).findByRole('alert')
    expect(alert).toHaveTextContent('Não foi possível carregar a origem do conceito.')
    // O cabeçalho já vem da tela, então o título e a linha de fatos ficam enquanto a rota falha
    expect(within(dialog).getByText(/^aparece em/)).toBeInTheDocument()

    restore()
    await outage
    fireEvent.click(within(alert).getByRole('button', { name: 'Tentar de novo' }))
    await panelOf(dialog, 5)
    expect(calls(spy, 'GET', '/knowledge-components/1/origin')).toHaveLength(2)
  })
})
