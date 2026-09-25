import { useEffect } from 'react'
import { Check, Circle, LoaderCircle } from 'lucide-react'

import { OutcomeMessage } from '../../../components/OutcomeMessage'
import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { ApiError } from '../../../http/client'
import type { GenerationJob } from '../api/knowledgeComponents'
import { GENERATION_STAGES, stageStateOf, type StageState } from '../knowledgeComponents'
import type { Extraction } from '../useExtraction'
import './ExtractionDialog.css'

interface ExtractionDialogProps {
  extraction: Extraction
  assignmentName: string
  // As contagens do resultado, que só chegam depois de a lista do exercício ser recarregada
  result: { knowledgeComponents: number; problemsCovered: number } | null
}

export function ExtractionDialog({ extraction, assignmentName, result }: ExtractionDialogProps) {
  const { isDialogOpen, isRunning, start, job, begin, close } = extraction
  useWarnBeforeLeaving(isRunning)
  const view = viewOf(extraction)

  return (
    <Dialog open={isDialogOpen} onClose={close} title={TITLES[view]} dismissible={!isRunning}>
      <DialogBody>
        <p className="extraction__subtitle">{assignmentName}</p>
        {view === 'running' ? <RunningStages job={job} /> : null}
        {view === 'done' ? <Done result={result} /> : null}
        {view === 'failed' ? <Failed detail={job?.error_message ?? null} /> : null}
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
              Revisar conceitos
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

type ExtractionView = 'running' | 'done' | 'failed' | 'refused'

const TITLES: Record<ExtractionView, string> = {
  running: 'Extraindo conceitos',
  done: 'Conceitos extraídos',
  failed: 'A extração não terminou',
  refused: 'Não foi possível começar a extração',
}

function viewOf({ isRunning, start, job }: Extraction): ExtractionView {
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

const STAGE_ICON: Record<StageState, typeof Check> = {
  done: Check,
  current: LoaderCircle,
  todo: Circle,
}

function RunningStages({ job }: { job: GenerationJob | undefined }) {
  return (
    <>
      <ol className="extraction-stages">
        {GENERATION_STAGES.map(({ stage, label }) => {
          const state = stageStateOf(stage, job)
          const Icon = STAGE_ICON[state]
          return (
            <li
              key={stage}
              className={`extraction-stages__item extraction-stages__item--${state}`}
              aria-current={state === 'current' ? 'step' : undefined}
            >
              <Icon className="extraction-stages__icon" size={17} aria-hidden="true" />
              <span className="extraction-stages__label">{label}</span>
              {state === 'current' && job?.progress_total ? (
                <span className="extraction-stages__progress mono">
                  {job.progress_done ?? 0} de {job.progress_total}
                </span>
              ) : null}
            </li>
          )
        })}
      </ol>
      <p className="extraction__note">
        Leva alguns minutos. Não feche esta página. Enquanto a extração roda, nenhum treino ou outra
        extração começa.
      </p>
    </>
  )
}

function Done({ result }: { result: ExtractionDialogProps['result'] }) {
  if (!result) return <p className="extraction__note">Carregando o resultado…</p>
  return (
    <>
      <div className="extraction-numbers">
        <div>
          <div className="extraction-numbers__value mono">{result.knowledgeComponents}</div>
          <div className="extraction-numbers__label">conceitos</div>
        </div>
        <div>
          <div className="extraction-numbers__value mono">{result.problemsCovered}</div>
          <div className="extraction-numbers__label">problemas cobertos</div>
        </div>
      </div>
      <p>A sugestão é do modelo, não um veredito. Revise antes de aprovar.</p>
    </>
  )
}

function Failed({ detail }: { detail: string | null }) {
  return (
    <>
      <p>O exercício continua como estava antes. Você pode tentar de novo.</p>
      {detail ? (
        <div className="extraction__detail">
          <span className="extraction__detail-title">Detalhe técnico</span>
          <span className="mono">{detail}</span>
        </div>
      ) : null}
    </>
  )
}
