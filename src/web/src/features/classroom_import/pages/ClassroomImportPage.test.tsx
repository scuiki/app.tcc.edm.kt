import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, renderWithClient } from '../../../test/renderWithClient'
import type { ClassroomSummary } from '../../classrooms/api/classrooms'
import type { ClassroomImportReport, DetectedUpload } from '../api/classroomImport'
import { ClassroomImportPage } from './ClassroomImportPage'

const EMPTY_CLASSROOM: ClassroomSummary = {
  id: 1,
  name: 'Algoritmos I',
  created_at: '2026-09-24T13:42:00+00:00',
  problem_count: 0,
  student_count: 0,
  status: 'awaiting_data',
}

const CLASSROOM_WITH_DATA: ClassroomSummary = {
  ...EMPTY_CLASSROOM,
  id: 2,
  name: 'CSEDM Spring 2019',
  problem_count: 50,
  student_count: 413,
  status: 'trained',
}

const RAW = '/app/data/1/raw/2026-09-25_pacote'

const DETECTED: DetectedUpload = {
  classroom_id: 1,
  raw_dir: RAW,
  main_tables: [`${RAW}/MainTable.csv`],
  code_snapshots: `${RAW}/CodeStates/CodeStates.csv`,
}

const IMPORTED: ClassroomImportReport = {
  has_fatal: false,
  checks: [
    {
      check: 'dedup_compile',
      severity: 'warning',
      message: '69627 evento(s) Compile plain descartado(s) no dedup mesmo-timestamp.',
    },
  ],
  dataset_summary: { n_students: 413, n_assignments: 2, n_problems: 50, n_submissions: 131943 },
  per_assignment: [
    { progsnap_assignment_id: 439, trainable: true },
    { progsnap_assignment_id: 487, trainable: false },
  ],
}

const REFUSED: ClassroomImportReport = {
  has_fatal: true,
  checks: [
    {
      check: 'missing_required_column',
      severity: 'fatal',
      message: 'coluna obrigatória ausente: Score.',
    },
  ],
  dataset_summary: {},
  per_assignment: [],
}

const BUSY: ClassroomImportReport = {
  ...REFUSED,
  checks: [
    { check: 'another_job_running', severity: 'fatal', message: 'Já existe um processamento.' },
  ],
}

interface FakeApiOptions {
  classrooms?: ClassroomSummary[]
  detected?: DetectedUpload
  failUpload?: boolean
  // Uma resposta por clique em Processar, na ordem
  reports?: ClassroomImportReport[]
}

function fakeApi({
  classrooms = [EMPTY_CLASSROOM],
  detected = DETECTED,
  failUpload = false,
  reports = [IMPORTED],
}: FakeApiOptions = {}) {
  const pending = [...reports]
  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const path = String(input)
    if (path === '/classrooms') return jsonResponse({ classrooms })
    if (path === '/classroom-imports') {
      return failUpload ? jsonResponse({}, 500) : jsonResponse(detected)
    }
    if (path === '/classroom-imports/process') return jsonResponse(pending.shift() ?? IMPORTED)
    throw new Error(`fetch inesperado ${init?.method ?? 'GET'} ${path}`)
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

function zipFile(name = 'pacote.zip') {
  return new File(['conteúdo'], name, { type: 'application/zip' })
}

async function pickFile(file = zipFile()) {
  const input = await screen.findByLabelText(/Arraste o arquivo/)
  fireEvent.change(input, { target: { files: [file] } })
}

function processButton() {
  return screen.getByRole('button', { name: /Processar dados|Processando/ })
}

function currentStep() {
  const steps = screen.getByRole('list', { name: 'Etapas da importação' })
  return within(steps)
    .getAllByRole('listitem')
    .find((item) => item.getAttribute('aria-current') === 'step')
}

describe('ClassroomImportPage, choosing the classroom and the file', () => {
  it('preselects the only classroom and shows what came in the package', async () => {
    const fetchSpy = fakeApi()
    renderWithClient(<ClassroomImportPage />)
    await pickFile()

    expect(await screen.findByText('pacote.zip')).toBeInTheDocument()
    expect(screen.getByText('MainTable.csv')).toBeInTheDocument()
    expect(screen.getByText('CodeStates/CodeStates.csv')).toBeInTheDocument()
    expect(screen.getByText(/Uma tabela de eventos encontrada/)).toBeInTheDocument()
    expect(processButton()).toBeEnabled()
    expect(currentStep()).toHaveTextContent('Turma e arquivo')

    const [, init] = fetchSpy.mock.calls.find(([path]) => path === '/classroom-imports')!
    const form = init!.body as FormData
    expect(form.get('classroom_id')).toBe('1')
    expect((form.get('file') as File).name).toBe('pacote.zip')
  })

  it('asks for the classroom before the file when there are several', async () => {
    fakeApi({ classrooms: [EMPTY_CLASSROOM, CLASSROOM_WITH_DATA] })
    renderWithClient(<ClassroomImportPage />)
    expect(await screen.findByText('Escolha a turma antes do arquivo')).toBeInTheDocument()
    expect(screen.getByLabelText(/Arraste o arquivo/)).toBeDisabled()

    fireEvent.change(screen.getByLabelText(/Turma/), { target: { value: '1' } })
    expect(screen.getByLabelText(/Arraste o arquivo/)).toBeEnabled()
  })

  it('warns that a classroom with data gets new exercises, and lets it go on', async () => {
    fakeApi({ classrooms: [CLASSROOM_WITH_DATA] })
    renderWithClient(<ClassroomImportPage />)
    expect(await screen.findByText(/Esta turma já tem dados/)).toBeInTheDocument()
    await pickFile()
    await screen.findByText('pacote.zip')
    expect(processButton()).toBeEnabled()
  })

  it('refuses a package without CodeStates.csv and lets the teacher pick another', async () => {
    fakeApi({ detected: { ...DETECTED, code_snapshots: null } })
    renderWithClient(<ClassroomImportPage />)
    await pickFile()

    expect(await screen.findByText('O pacote não tem CodeStates.csv')).toBeInTheDocument()
    expect(processButton()).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Escolher outro arquivo' }))
    expect(screen.getByLabelText(/Arraste o arquivo/)).toBeInTheDocument()
  })

  it('makes the teacher choose when the package brings two events tables', async () => {
    const fetchSpy = fakeApi({
      detected: { ...DETECTED, main_tables: [`${RAW}/a/MainTable.csv`, `${RAW}/b/MainTable.csv`] },
    })
    renderWithClient(<ClassroomImportPage />)
    await pickFile()

    expect(await screen.findByText(/traz 2 tabelas de eventos/)).toBeInTheDocument()
    expect(processButton()).toBeDisabled()
    fireEvent.click(screen.getByRole('radio', { name: 'b/MainTable.csv' }))
    fireEvent.click(processButton())

    expect(await screen.findByText('pacote.zip importado em Algoritmos I.')).toBeInTheDocument()
    const processCall = fetchSpy.mock.calls.find(([path]) => path === '/classroom-imports/process')
    expect(JSON.parse(String(processCall![1]!.body)).main_table).toBe(`${RAW}/b/MainTable.csv`)
  })

  it('shows the generic message when the upload fails', async () => {
    fakeApi({ failUpload: true })
    renderWithClient(<ClassroomImportPage />)
    await pickFile()
    expect(await screen.findByText('Não foi possível abrir o arquivo')).toBeInTheDocument()
  })

  it('refuses a file over 512 MB without sending it', async () => {
    const fetchSpy = fakeApi()
    renderWithClient(<ClassroomImportPage />)
    const huge = zipFile('enorme.zip')
    Object.defineProperty(huge, 'size', { value: 600 * 1024 * 1024 })
    await pickFile(huge)

    expect(await screen.findByText('O arquivo passa de 512 MB')).toBeInTheDocument()
    expect(fetchSpy).not.toHaveBeenCalledWith('/classroom-imports', expect.anything())
  })

  it('discards the uploaded file when the classroom changes', async () => {
    fakeApi({ classrooms: [EMPTY_CLASSROOM, CLASSROOM_WITH_DATA] })
    renderWithClient(<ClassroomImportPage />)
    fireEvent.change(await screen.findByLabelText(/Turma/), { target: { value: '1' } })
    await pickFile()
    await screen.findByText('pacote.zip')

    fireEvent.change(screen.getByLabelText(/Turma/), { target: { value: '2' } })
    expect(screen.queryByText('pacote.zip')).not.toBeInTheDocument()
    expect(screen.getByLabelText(/Arraste o arquivo/)).toBeEnabled()
  })

  it('sends to the classrooms page when there is no classroom yet', async () => {
    fakeApi({ classrooms: [] })
    renderWithClient(<ClassroomImportPage />)
    expect(await screen.findByText('Nenhuma turma ainda')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ir para Turmas' })).toHaveAttribute(
      'href',
      '#/classrooms',
    )
  })
})

describe('ClassroomImportPage, processing', () => {
  it('shows the summary, the exercises and the warnings after importing', async () => {
    fakeApi()
    renderWithClient(<ClassroomImportPage />)
    await pickFile()
    await screen.findByText('pacote.zip')
    fireEvent.click(processButton())

    expect(await screen.findByText('pacote.zip importado em Algoritmos I.')).toBeInTheDocument()
    expect(screen.getByText(/1 dos 2 exercícios estão prontos/)).toBeInTheDocument()
    expect(screen.getByText('131.943')).toBeInTheDocument()
    const rows = screen.getAllByRole('row')
    expect(rows.find((row) => row.textContent?.includes('Assignment 439'))).toHaveTextContent(
      'Pronto para conceitos',
    )
    expect(rows.find((row) => row.textContent?.includes('Assignment 487'))).toHaveTextContent(
      'Só estatísticas',
    )
    expect(screen.getByText('Compilações repetidas descartadas')).toBeInTheDocument()
    expect(screen.getByText(/69627 evento\(s\) Compile plain/)).toBeInTheDocument()
    expect(currentStep()).toHaveTextContent('Conferir')

    fireEvent.click(screen.getByRole('button', { name: 'Extrair conceitos' }))
    expect(window.location.hash).toBe('#/knowledge-components?classroom=1')
    window.location.hash = ''
  })

  it('keeps the choices and lists the failed check when the package is refused', async () => {
    fakeApi({ reports: [REFUSED] })
    renderWithClient(<ClassroomImportPage />)
    await pickFile()
    await screen.findByText('pacote.zip')
    fireEvent.click(processButton())

    expect(await screen.findByText('A tabela de eventos está incompleta')).toBeInTheDocument()
    expect(screen.getByText('coluna obrigatória ausente: Score.')).toBeInTheDocument()
    expect(screen.getByText('pacote.zip')).toBeInTheDocument()
    expect(currentStep()).toHaveTextContent('Processar')
  })

  it('says the system is busy and retries with the same choices', async () => {
    const fetchSpy = fakeApi({ reports: [BUSY, IMPORTED] })
    renderWithClient(<ClassroomImportPage />)
    await pickFile()
    await screen.findByText('pacote.zip')
    fireEvent.click(processButton())

    expect(await screen.findByText('Outro processo está rodando')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))
    expect(await screen.findByText('pacote.zip importado em Algoritmos I.')).toBeInTheDocument()
    const processCalls = fetchSpy.mock.calls.filter(
      ([path]) => path === '/classroom-imports/process',
    )
    expect(processCalls).toHaveLength(2)
    expect(processCalls[1][1]!.body).toBe(processCalls[0][1]!.body)
  })

  it('starts over clean from Importar outros dados', async () => {
    fakeApi()
    renderWithClient(<ClassroomImportPage />)
    await pickFile()
    await screen.findByText('pacote.zip')
    fireEvent.click(processButton())
    fireEvent.click(await screen.findByRole('button', { name: 'Importar outros dados' }))

    await waitFor(() => expect(currentStep()).toHaveTextContent('Turma e arquivo'))
    expect(screen.getByLabelText(/Arraste o arquivo/)).toBeInTheDocument()
    expect(screen.queryByText('pacote.zip')).not.toBeInTheDocument()
  })
})
