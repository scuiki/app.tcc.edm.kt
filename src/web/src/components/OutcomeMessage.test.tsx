import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { OutcomeMessage } from './OutcomeMessage'

describe('OutcomeMessage', () => {
  it('announces a refusal as an alert, with the title and the explanation', () => {
    render(
      <OutcomeMessage tone="danger" title="Não foi possível abrir o arquivo">
        Confira o pacote.
      </OutcomeMessage>,
    )
    const alert = screen.getByRole('alert')
    expect(alert).toHaveTextContent('Não foi possível abrir o arquivo')
    expect(alert).toHaveTextContent('Confira o pacote.')
    expect(alert.querySelector('svg')).not.toBeNull()
  })

  it('announces a neutral outcome as a status', () => {
    render(
      <OutcomeMessage tone="neutral" title="Outro processo está rodando">
        Tente depois.
      </OutcomeMessage>,
    )
    const status = screen.getByRole('status')
    expect(status).toHaveTextContent('Outro processo está rodando')
    // O ! fica só para a recusa, então o neutro não leva ícone
    expect(status.querySelector('svg')).toBeNull()
  })
})
