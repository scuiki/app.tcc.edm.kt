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

  it('renders without description nor action', () => {
    render(<PageHeader title="Minhas turmas" />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Minhas turmas')
  })
})
