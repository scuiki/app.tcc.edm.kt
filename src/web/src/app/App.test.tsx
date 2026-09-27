import { act, screen, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, renderWithClient } from '../test/renderWithClient'
import { App } from './App'

function goTo(hash: string) {
  act(() => {
    window.location.hash = hash
    window.dispatchEvent(new HashChangeEvent('hashchange'))
  })
}

beforeEach(() => {
  // Toda lista começa vazia, porque aqui só interessa o casco
  vi.spyOn(globalThis, 'fetch').mockImplementation(async () =>
    jsonResponse({ assignments: [], classrooms: [] }),
  )
})

afterEach(() => {
  window.location.hash = ''
  vi.restoreAllMocks()
})

describe('App', () => {
  it('shows the tool icon and the two fixed entries of the menu', () => {
    renderWithClient(<App />)
    expect(screen.getByRole('img', { name: 'EDM·KT, ferramenta docente' })).toBeInTheDocument()
    const menu = screen.getByRole('navigation', { name: 'Navegação principal' })
    expect(within(menu).getByRole('link', { name: 'Turmas' })).toBeInTheDocument()
    expect(within(menu).getByRole('link', { name: 'Importar dados' })).toBeInTheDocument()
  })

  it('opens Turmas when there is no hash', () => {
    renderWithClient(<App />)
    expect(screen.getByRole('link', { name: 'Turmas' })).toHaveAttribute('aria-current', 'page')
  })

  it('follows the hash to the page it names', () => {
    renderWithClient(<App />)
    goTo('#/classroom-imports')
    expect(screen.getByRole('link', { name: 'Importar dados' })).toHaveAttribute(
      'aria-current',
      'page',
    )
  })

  it('says the page was not found for an unknown hash', () => {
    renderWithClient(<App />)
    goTo('#/nao-existe')
    expect(screen.getByText('Página não encontrada')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Ir para Turmas' })).toBeInTheDocument()
  })

  it('treats a non numeric id in the address as not found', () => {
    renderWithClient(<App />)
    goTo('#/classrooms/abc')
    expect(screen.getByText('Página não encontrada')).toBeInTheDocument()
  })
})
