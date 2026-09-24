import { act, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { jsonResponse, renderWithClient } from '../test/renderWithClient'
import { App } from './App'
import { ROUTES } from './routes'

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
  it('shows the tool icon and one menu link per page', () => {
    renderWithClient(<App />)
    expect(screen.getByRole('img', { name: 'EDM·KT, ferramenta docente' })).toBeInTheDocument()
    const menu = screen.getByRole('navigation', { name: 'Navegação principal' })
    for (const route of ROUTES) {
      expect(menu).toContainElement(screen.getByRole('link', { name: route.label }))
    }
  })

  it('opens the first page of the menu when there is no hash', () => {
    renderWithClient(<App />)
    expect(screen.getByRole('link', { name: ROUTES[0].label })).toHaveAttribute(
      'aria-current',
      'page',
    )
  })

  it('follows the hash to the page it names', () => {
    renderWithClient(<App />)
    const last = ROUTES[ROUTES.length - 1]
    goTo(`#${last.path}`)
    expect(screen.getByRole('link', { name: last.label })).toHaveAttribute('aria-current', 'page')
  })

  it('says the page was not found for an unknown hash', () => {
    renderWithClient(<App />)
    goTo('#/nao-existe')
    expect(screen.getByText('Página não encontrada')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: `Ir para ${ROUTES[0].label}` })).toBeInTheDocument()
  })
})
