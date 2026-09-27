import { useEffect } from 'react'

import { OutcomeMessage } from '../../../components/OutcomeMessage'
import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { StageList } from '../../../components/ui/StageList'
import { ApiError } from '../../../http/client'
import { formatPercent } from '../../../lib/format'
import { epochProgress, stageStateOf, TRAINING_STAGES } from '../trainingStages'
import type { Training } from '../useTraining'
import { LossChart } from './LossChart'
import './TrainingDialog.css'

interface TrainingDialogProps {
  training: Training
  assignmentName: string
}

export function TrainingDialog({ training, assignmentName }: TrainingDialogProps) {
  const { isDialogOpen, isRunning, start, job, epochs, begin, close } = training
  useWarnBeforeLeaving(isRunning)
  const view = viewOf(training)

  return (
    <Dialog open={isDialogOpen} onClose={close} title={TITLES[view]} dismissible={!isRunning}>
      <DialogBody>
        <p className="training__subtitle">{assignmentName}</p>
        {view === 'running' ? (
          <>
            <StageList
              items={TRAINING_STAGES.map(({ stage, label }) => ({
                key: stage,
                label,
                state: stageStateOf(stage, job),
                progress: stage === 'training' ? epochProgress(job) : null,
              }))}
            />
            {epochs.length > 0 ? (
              <LossChart epochs={epochs} totalEpochs={job?.total_epochs ?? null} />
            ) : null}
            <p className="training__note">
              Leva alguns minutos. Não feche esta página. Enquanto o treino roda, nenhuma extração
              ou outro treino começa.
            </p>
          </>
        ) : null}
        {view === 'done' ? (
          <>
            <p>
              O modelo foi treinado e publicado. A Análise agora mostra o domínio estimado por
              problema, conceito e aluno.
            </p>
            {epochs.length > 0 ? (
              <LossChart epochs={epochs} totalEpochs={job?.total_epochs ?? null} />
            ) : null}
            {job?.java_parse_rate != null ? (
              <p className="training__fact">
                Código dos alunos lido pelo parser Java{' '}
                <span className="mono">{formatPercent(job.java_parse_rate)}</span>
              </p>
            ) : null}
          </>
        ) : null}
        {view === 'failed' ? (
          <>
            <p>O exercício continua como estava antes. Você pode tentar de novo.</p>
            {job?.error_message ? (
              <div className="training__detail">
                <span className="training__detail-title">Detalhe técnico</span>
                <span className="mono">{job.error_message}</span>
              </div>
            ) : null}
          </>
        ) : null}
        {view === 'refused' ? (
          <OutcomeMessage tone="danger" title="O pedido foi recusado">
            {start.error instanceof ApiError && start.error.detail
              ? start.error.detail
              : 'Verifique se a API está no ar e tente de novo.'}
          </OutcomeMessage>
        ) : null}
      </DialogBody>
      {view === 'running' ? null : (
        <DialogFooter>
          {view === 'done' ? (
            <Button variant="primary" onClick={close}>
              Ver a análise
            </Button>
          ) : (
            <>
              <Button variant="secondary" onClick={close}>
                Fechar
              </Button>
              <Button variant="primary" onClick={begin}>
                Tentar de novo
              </Button>
            </>
          )}
        </DialogFooter>
      )}
    </Dialog>
  )
}

type TrainingView = 'running' | 'done' | 'failed' | 'refused'

const TITLES: Record<TrainingView, string> = {
  running: 'Treino em andamento',
  done: 'Modelo treinado',
  failed: 'O treino não terminou',
  refused: 'Não foi possível começar o treino',
}

function viewOf({ isRunning, start, job }: Training): TrainingView {
  if (start.isError) return 'refused'
  if (isRunning) return 'running'
  return job?.status === 'done' ? 'done' : 'failed'
}

// Sincroniza com a janela, o único jeito de pedir confirmação antes de fechar ou recarregar a aba
function useWarnBeforeLeaving(active: boolean) {
  useEffect(() => {
    if (!active) return
    const warn = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener('beforeunload', warn)
    return () => window.removeEventListener('beforeunload', warn)
  }, [active])
}
