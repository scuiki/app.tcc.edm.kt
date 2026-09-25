import { fireEvent, render, screen } from '@testing-library/react'
import type { UseQueryResult } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

import { EmptyState, ErrorState, LoadingState, QueryStates } from './states'

// Só os campos que o QueryStates lê, sem montar um QueryClient
function fakeQuery<T>(fields: Partial<UseQueryResult<T>>): UseQueryResult<T> {
  return { isPending: false, isError: false, refetch: vi.fn(), ...fields } as UseQueryResult<T>
}

describe('LoadingState', () => {
  it('names what is being loaded', () => {
    render(<LoadingState label="Carregando turmas…" />)
    expect(screen.getByRole('status')).toHaveTextContent('Carregando turmas…')
  })
})

describe('ErrorState', () => {
  it('shows a default message and no retry button without onRetry', () => {
    render(<ErrorState />)
    expect(screen.getByRole('alert')).toHaveTextContent('Verifique se a API está no ar')
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('calls onRetry from the retry button', () => {
    const onRetry = vi.fn()
    render(<ErrorState message="Falhou." onRetry={onRetry} />)
    fireEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))
    expect(onRetry).toHaveBeenCalledOnce()
  })
})

describe('EmptyState', () => {
  it('shows the title, the text and the action', () => {
    render(
      <EmptyState
        title="Nenhuma turma ainda"
        text="Cadastre a primeira turma."
        action={<button type="button">Nova turma</button>}
      />,
    )
    expect(screen.getByText('Nenhuma turma ainda')).toBeInTheDocument()
    expect(screen.getByText('Cadastre a primeira turma.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nova turma' })).toBeInTheDocument()
  })
})

describe('QueryStates', () => {
  const content = (items: string[]) => <p>{items.join(', ')}</p>

  it('shows the loading label while pending', () => {
    render(
      <QueryStates query={fakeQuery<string[]>({ isPending: true })} loadingLabel="Carregando…">
        {content}
      </QueryStates>,
    )
    expect(screen.getByRole('status')).toHaveTextContent('Carregando…')
  })

  it('shows the error with a retry that refetches', () => {
    const query = fakeQuery<string[]>({ isError: true })
    render(
      <QueryStates query={query} loadingLabel="Carregando…" errorMessage="Não carregou.">
        {content}
      </QueryStates>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Não carregou.')
    fireEvent.click(screen.getByRole('button', { name: 'Tentar de novo' }))
    expect(query.refetch).toHaveBeenCalledOnce()
  })

  it('keeps the content when a background refetch fails', () => {
    render(
      <QueryStates
        query={fakeQuery<string[]>({ isError: true, data: ['a', 'b'] })}
        loadingLabel="Carregando…"
      >
        {content}
      </QueryStates>,
    )
    expect(screen.getByText('a, b')).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })

  it('shows the empty node when the caller says the data is empty', () => {
    render(
      <QueryStates
        query={fakeQuery<string[]>({ data: [] })}
        loadingLabel="Carregando…"
        isEmpty={(items) => items.length === 0}
        empty={<p>Vazio</p>}
      >
        {content}
      </QueryStates>,
    )
    expect(screen.getByText('Vazio')).toBeInTheDocument()
  })

  it('renders the content with the data otherwise', () => {
    render(
      <QueryStates
        query={fakeQuery<string[]>({ data: ['a', 'b'] })}
        loadingLabel="Carregando…"
        isEmpty={(items) => items.length === 0}
        empty={<p>Vazio</p>}
      >
        {content}
      </QueryStates>,
    )
    expect(screen.getByText('a, b')).toBeInTheDocument()
  })
})
