import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { TrainedModelInfoNote } from './TrainedModelInfoNote'

describe('TrainedModelInfoNote', () => {
  it('shows the AUC and the training date when a model is published', () => {
    render(<TrainedModelInfoNote firstAttemptAuc={0.76} trainedAt="2026-06-21T00:00:00Z" />)
    const note = screen.getByRole('note')
    expect(note).toHaveTextContent('AUC da turma 76%')
    expect(note).toHaveTextContent('2026-06-21T00:00:00Z')
    expect(note).toHaveTextContent('Não é um veredito.')
  })

  it('says the model is not trained yet otherwise', () => {
    render(<TrainedModelInfoNote firstAttemptAuc={null} trainedAt={null} />)
    expect(screen.getByRole('note')).toHaveTextContent(
      'Modelo ainda não treinado para este assignment.',
    )
  })
})
