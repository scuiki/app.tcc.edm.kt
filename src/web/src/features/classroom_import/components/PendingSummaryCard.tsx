import type { ReactNode } from 'react'
import { LoaderCircle } from 'lucide-react'

import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import type { ImportCheck } from '../api/classroomImport'
import { checkTitle } from '../importReport'
import { OutcomeMessage } from './OutcomeMessage'
import './ImportCards.css'

// O que ocupa o resumo entre a escolha do pacote e os dados gravados
export type PendingStatus =
  | { kind: 'waiting' }
  | { kind: 'processing' }
  | { kind: 'busy' }
  | { kind: 'refused'; fatalChecks: ImportCheck[] }
  | { kind: 'failed' }

const PLACEHOLDER_LABELS = ['alunos', 'problemas', 'exercícios', 'submissões']

interface PendingSummaryCardProps {
  status: PendingStatus
  onRetry: () => void
}

export function PendingSummaryCard({ status, onRetry }: PendingSummaryCardProps) {
  return (
    <Card title="Resumo dos dados">
      <div className="import-card__body">
        {status.kind === 'waiting' ? <Waiting /> : null}
        {status.kind === 'processing' ? <Processing /> : null}
        {status.kind === 'busy' ? (
          <Retryable
            onRetry={onRetry}
            intro="Um treino ou uma extração segurava a trava. Nada foi gravado."
          >
            <OutcomeMessage tone="neutral" title="Outro processo está rodando">
              Só um processo roda por vez, e agora há um treino ou uma extração de conceitos em
              andamento. Seus dados continuam aqui, é só tentar de novo quando ele terminar.
            </OutcomeMessage>
          </Retryable>
        ) : null}
        {status.kind === 'refused' ? <Refused fatalChecks={status.fatalChecks} /> : null}
        {status.kind === 'failed' ? (
          <Retryable onRetry={onRetry} intro="O pedido não chegou ao fim.">
            <OutcomeMessage tone="danger" title="Não foi possível processar">
              Verifique se a API está no ar e tente de novo. O que você escolheu continua aqui.
            </OutcomeMessage>
          </Retryable>
        ) : null}
      </div>
    </Card>
  )
}

function Waiting() {
  return (
    <>
      <div className="summary-numbers summary-numbers--placeholder">
        {PLACEHOLDER_LABELS.map((label) => (
          <div key={label}>
            <div className="summary-numbers__skeleton" />
            <div className="summary-numbers__label">{label}</div>
          </div>
        ))}
      </div>
      <div className="import-card__rule" />
      <div className="pending-text">
        <span className="pending-text__title">O resumo aparece depois do processamento</span>
        <p>
          Ao processar, o sistema valida o formato, separa os exercícios, conta alunos e problemas e
          grava os dados na turma. Se algo impedir a gravação, nada é salvo e você corrige e tenta
          de novo.
        </p>
      </div>
    </>
  )
}

function Processing() {
  return (
    <div className="pending-text" role="status">
      <span className="pending-text__title pending-text__title--with-icon">
        <LoaderCircle className="pending-text__spinner" size={18} aria-hidden="true" />
        Processando o pacote
      </span>
      <p>
        Validando o formato, separando os exercícios e gravando os dados. Leva de alguns segundos a
        um minuto. Não feche esta página.
      </p>
    </div>
  )
}

function Refused({ fatalChecks }: { fatalChecks: ImportCheck[] }) {
  return (
    <>
      <p className="pending-intro">Uma verificação obrigatória falhou. Nada foi gravado.</p>
      <div className="import-card__rule" />
      {fatalChecks.map((check) => (
        <OutcomeMessage
          key={`${check.check}-${check.message}`}
          tone="danger"
          title={checkTitle(check)}
        >
          {check.message}
        </OutcomeMessage>
      ))}
    </>
  )
}

interface RetryableProps {
  intro: string
  onRetry: () => void
  children: ReactNode
}

function Retryable({ intro, onRetry, children }: RetryableProps) {
  return (
    <>
      <p className="pending-intro">{intro}</p>
      <div className="import-card__rule" />
      {children}
      <div className="pending-actions">
        <Button variant="primary" onClick={onRetry}>
          Tentar de novo
        </Button>
      </div>
    </>
  )
}
