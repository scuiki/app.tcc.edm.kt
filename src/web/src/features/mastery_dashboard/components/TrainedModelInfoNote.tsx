import { formatPercent } from '../../../lib/format'

interface TrainedModelInfoNoteProps {
  firstAttemptAuc: number | null
  trainedAt: string | null
}

// Sempre visível, para um número derivado do modelo nunca ser lido como veredito
export function TrainedModelInfoNote({ firstAttemptAuc, trainedAt }: TrainedModelInfoNoteProps) {
  return (
    <div
      role="note"
      className={`model-note model-note--${firstAttemptAuc == null ? 'untrained' : 'trained'}`}
    >
      {firstAttemptAuc == null ? (
        <p>
          Modelo ainda não treinado para este assignment. A EDA abaixo está disponível mesmo assim.
        </p>
      ) : (
        <p>
          Sinal com incerteza — AUC da turma {formatPercent(firstAttemptAuc)}, dados de {trainedAt}.
          Não é um veredito.
        </p>
      )}
    </div>
  )
}
