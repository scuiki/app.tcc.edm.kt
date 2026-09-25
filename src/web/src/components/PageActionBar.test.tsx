import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PageActionBar } from './PageActionBar'

describe('PageActionBar', () => {
  it('shows what the next click does next to the buttons', () => {
    render(
      <PageActionBar message="Processar grava os dados na turma.">
        <button type="button">Processar dados</button>
      </PageActionBar>,
    )
    expect(screen.getByText('Processar grava os dados na turma.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Processar dados' })).toBeInTheDocument()
  })
})
