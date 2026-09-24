import { render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ErrorBoundary } from './ErrorBoundary'

function Broken(): never {
  throw new Error('quebrou')
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ErrorBoundary', () => {
  it('renders the children when nothing throws', () => {
    render(
      <ErrorBoundary>
        <p>Conteúdo</p>
      </ErrorBoundary>,
    )
    expect(screen.getByText('Conteúdo')).toBeInTheDocument()
  })

  it('turns a render exception into a message with a way out', () => {
    // O React registra no console o erro que o boundary pegou
    vi.spyOn(console, 'error').mockImplementation(() => {})
    render(
      <ErrorBoundary>
        <Broken />
      </ErrorBoundary>,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Algo deu errado nesta tela.')
    expect(screen.getByRole('button', { name: 'Tentar de novo' })).toBeInTheDocument()
  })
})
