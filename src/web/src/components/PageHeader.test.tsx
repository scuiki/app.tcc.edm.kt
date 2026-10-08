import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PageHeader } from './PageHeader'

describe('PageHeader', () => {
  it('renders the page title as the only h1, with the description and the action', () => {
    render(
      <PageHeader
        title="Minhas turmas"
        description="Crie e gerencie suas turmas"
        action={<button type="button">Nova turma</button>}
      />,
    )
    expect(screen.getByRole('heading', { level: 1, name: 'Minhas turmas' })).toBeInTheDocument()
    expect(screen.getByText('Crie e gerencie suas turmas')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Nova turma' })).toBeInTheDocument()
  })

  it('shows the badge beside the title and outside the heading', () => {
    render(<PageHeader title="Assignment 439" badge={<span>Treinado</span>} />)
    const heading = screen.getByRole('heading', { level: 1, name: 'Assignment 439' })
    expect(heading).not.toHaveTextContent('Treinado')
    expect(screen.getByText('Treinado')).toBeInTheDocument()
  })

  it('shows the facts line below the title row and outside the heading', () => {
    render(
      <PageHeader
        title="Assignment 439"
        badge={<span>Rascunho de conceitos</span>}
        facts={<p>10 problemas, 25 conceitos</p>}
      />,
    )
    const heading = screen.getByRole('heading', { level: 1, name: 'Assignment 439' })
    const facts = screen.getByText('10 problemas, 25 conceitos')
    expect(heading).not.toHaveTextContent('10 problemas')
    expect(heading.parentElement).not.toContainElement(facts)
    expect(heading.compareDocumentPosition(facts) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })

  it('renders without description nor action', () => {
    render(<PageHeader title="Minhas turmas" />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Minhas turmas')
  })
})
