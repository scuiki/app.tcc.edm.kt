import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, renderWithClient } from '../../../test/renderWithClient'
import type { ClassroomSummary } from '../api/classrooms'
import { ClassroomsPage } from './ClassroomsPage'

const ALGORITMOS: ClassroomSummary = {
  id: 1,
  name: 'Algoritmos I',
  created_at: '2026-09-24T13:42:00+00:00',
  problem_count: 0,
  student_count: 0,
  status: 'awaiting_data',
}

const CSEDM: ClassroomSummary = {
  id: 2,
  name: 'CSEDM Spring 2019',
  created_at: '2026-06-21T22:07:00+00:00',
  problem_count: 50,
  student_count: 1413,
  status: 'trained',
}

interface FakeApiOptions {
  classrooms?: ClassroomSummary[]
  failList?: boolean
}

// Uma api em memória que responde como o backend, com o 409 para nome repetido
function fakeApi({ classrooms = [ALGORITMOS, CSEDM], failList = false }: FakeApiOptions = {}) {
  let rows = [...classrooms]
  const isTaken = (name: string, ownId?: number) =>
    rows.some((row) => row.id !== ownId && row.name.toLowerCase() === name.toLowerCase())

  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const path = String(input)
    const method = init?.method ?? 'GET'
    const body = init?.body ? JSON.parse(String(init.body)) : undefined
    const id = Number(path.split('/')[2])

    if (method === 'GET' && path === '/classrooms') {
      return failList ? jsonResponse({}, 503) : jsonResponse({ classrooms: rows })
    }
    if (method === 'POST' && path === '/classrooms') {
      if (isTaken(body.name)) return jsonResponse({ detail: 'já existe' }, 409)
      const created = {
        ...ALGORITMOS,
        id: 99,
        name: body.name,
        created_at: '2026-09-25T12:00:00+00:00',
      }
      rows = [...rows, created]
      return jsonResponse({ id: 99, name: body.name, created_at: created.created_at }, 201)
    }
    if (method === 'PUT') {
      if (isTaken(body.name, id)) return jsonResponse({ detail: 'já existe' }, 409)
      rows = rows.map((row) => (row.id === id ? { ...row, name: body.name } : row))
      return jsonResponse({ id, name: body.name, created_at: '' })
    }
    if (method === 'DELETE') {
      rows = rows.filter((row) => row.id !== id)
      return jsonResponse({ deleted_classroom_id: id })
    }
    throw new Error(`fetch inesperado ${method} ${path}`)
  })
}

afterEach(() => {
  vi.restoreAllMocks()
})

async function findRow(name: string) {
  const cell = await screen.findByRole('cell', { name })
  return cell.closest('tr') as HTMLElement
}

describe('ClassroomsPage, the table', () => {
  it('shows each classroom with its counts, date and status', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    const csedm = await findRow('CSEDM Spring 2019')
    expect(within(csedm).getByText('50')).toBeInTheDocument()
    expect(within(csedm).getByText('1.413')).toBeInTheDocument()
    expect(within(csedm).getByText('21/06/2026')).toBeInTheDocument()
    expect(within(csedm).getByText('Modelo treinado')).toBeInTheDocument()
    expect(screen.getByText('2 turmas')).toBeInTheDocument()
  })

  it('links each name to the page of the classroom', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    expect(await screen.findByRole('link', { name: 'CSEDM Spring 2019' })).toHaveAttribute(
      'href',
      '#/classrooms/2',
    )
  })

  it('shows a dash instead of zero for a classroom without data', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    const algoritmos = await findRow('Algoritmos I')
    expect(within(algoritmos).getAllByText('—')).toHaveLength(2)
    expect(within(algoritmos).getByText('Aguardando dados')).toBeInTheDocument()
  })

  it('filters by name, ignoring case and accents', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    fireEvent.change(screen.getByLabelText('Buscar turma'), { target: { value: 'ALGORÍTMOS' } })
    expect(screen.getByRole('cell', { name: 'Algoritmos I' })).toBeInTheDocument()
    expect(screen.queryByRole('cell', { name: 'CSEDM Spring 2019' })).not.toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Buscar turma'), { target: { value: 'xyz' } })
    expect(screen.getByText('Nenhuma turma com esse nome.')).toBeInTheDocument()
  })

  it('lists the recent activity, newest first', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    const items = within(screen.getByRole('list')).getAllByRole('listitem')
    expect(items[0]).toHaveTextContent('Algoritmos I foi criada')
    expect(items[1]).toHaveTextContent('CSEDM Spring 2019 foi criada')
  })

  it('shows the empty state, and its action opens the dialog', async () => {
    fakeApi({ classrooms: [] })
    renderWithClient(<ClassroomsPage />)
    expect(await screen.findByText('Nenhuma turma ainda')).toBeInTheDocument()
    expect(screen.queryByText('Atividade recente')).not.toBeInTheDocument()
    const emptyState = screen.getByText('Nenhuma turma ainda').parentElement as HTMLElement
    fireEvent.click(within(emptyState).getByRole('button', { name: 'Nova turma' }))
    expect(screen.getByRole('dialog', { name: 'Nova turma' })).toBeInTheDocument()
  })

  it('shows the error with a retry when the list fails', async () => {
    fakeApi({ failList: true })
    renderWithClient(<ClassroomsPage />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Verifique se a API está no ar')
    expect(screen.getByRole('button', { name: 'Tentar de novo' })).toBeInTheDocument()
  })
})

describe('ClassroomsPage, creating and renaming', () => {
  it('creates a classroom, closes the dialog and shows it in the table', async () => {
    const fetchSpy = fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    fireEvent.click(screen.getByRole('button', { name: 'Nova turma' }))
    const dialog = screen.getByRole('dialog', { name: 'Nova turma' })
    fireEvent.change(within(dialog).getByLabelText(/Nome/), { target: { value: '  Turma B  ' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Criar' }))

    expect(await screen.findByRole('cell', { name: 'Turma B' })).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(fetchSpy).toHaveBeenCalledWith(
      '/classrooms',
      expect.objectContaining({ method: 'POST', body: '{"name":"Turma B"}' }),
    )
  })

  it('keeps Criar disabled while the name is blank', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    fireEvent.click(screen.getByRole('button', { name: 'Nova turma' }))
    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByRole('button', { name: 'Criar' })).toBeDisabled()
    fireEvent.change(within(dialog).getByLabelText(/Nome/), { target: { value: '   ' } })
    expect(within(dialog).getByRole('button', { name: 'Criar' })).toBeDisabled()
  })

  it('shows a repeated name on the field without closing, and clears it on typing', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    fireEvent.click(screen.getByRole('button', { name: 'Nova turma' }))
    const dialog = screen.getByRole('dialog')
    const input = within(dialog).getByLabelText(/Nome/)
    fireEvent.change(input, { target: { value: 'csedm spring 2019' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Criar' }))

    expect(
      await within(dialog).findByText('Você já tem uma turma com esse nome.'),
    ).toBeInTheDocument()
    expect(input).toHaveAttribute('aria-invalid', 'true')
    fireEvent.change(input, { target: { value: 'csedm spring 2020' } })
    expect(
      within(dialog).queryByText('Você já tem uma turma com esse nome.'),
    ).not.toBeInTheDocument()
  })

  it('opens clean after cancelling a half-typed name', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    fireEvent.click(screen.getByRole('button', { name: 'Nova turma' }))
    fireEvent.change(screen.getByLabelText(/Nome/), { target: { value: 'Rascunho' } })
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))

    fireEvent.click(screen.getByRole('button', { name: 'Nova turma' }))
    expect(screen.getByLabelText(/Nome/)).toHaveValue('')
  })

  it('renames with the current name prefilled', async () => {
    const fetchSpy = fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    fireEvent.click(screen.getByRole('button', { name: 'Renomear Algoritmos I' }))
    const dialog = screen.getByRole('dialog', { name: 'Renomear turma' })
    const input = within(dialog).getByLabelText(/Nome/)
    expect(input).toHaveValue('Algoritmos I')
    fireEvent.change(input, { target: { value: 'Algoritmos II' } })
    fireEvent.click(within(dialog).getByRole('button', { name: 'Salvar' }))

    expect(await screen.findByRole('cell', { name: 'Algoritmos II' })).toBeInTheDocument()
    expect(fetchSpy).toHaveBeenCalledWith(
      '/classrooms/1',
      expect.objectContaining({ method: 'PUT' }),
    )
  })
})

describe('ClassroomsPage, removing', () => {
  it('says what goes away and removes after confirming', async () => {
    const fetchSpy = fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('CSEDM Spring 2019')
    fireEvent.click(screen.getByRole('button', { name: 'Excluir CSEDM Spring 2019' }))
    const dialog = screen.getByRole('alertdialog', { name: 'Excluir CSEDM Spring 2019?' })
    expect(dialog).toHaveTextContent(
      'Saem junto 50 problemas, os conceitos e os modelos treinados dela.',
    )
    fireEvent.click(within(dialog).getByRole('button', { name: 'Excluir turma' }))

    await waitFor(() =>
      expect(screen.queryByRole('cell', { name: 'CSEDM Spring 2019' })).not.toBeInTheDocument(),
    )
    expect(fetchSpy).toHaveBeenCalledWith(
      '/classrooms/2',
      expect.objectContaining({ method: 'DELETE' }),
    )
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
  })

  it('says a classroom without data has nothing imported yet', async () => {
    fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    fireEvent.click(screen.getByRole('button', { name: 'Excluir Algoritmos I' }))
    expect(screen.getByRole('alertdialog')).toHaveTextContent(
      'A turma ainda não tem dados importados.',
    )
  })

  it('keeps the classroom when cancelling', async () => {
    const fetchSpy = fakeApi()
    renderWithClient(<ClassroomsPage />)
    await findRow('Algoritmos I')
    fireEvent.click(screen.getByRole('button', { name: 'Excluir Algoritmos I' }))
    fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(screen.queryByRole('alertdialog')).not.toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'Algoritmos I' })).toBeInTheDocument()
    expect(fetchSpy).not.toHaveBeenCalledWith('/classrooms/1', expect.anything())
  })
})
