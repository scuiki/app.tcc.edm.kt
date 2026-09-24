import { useState } from 'react'

import { PageHeader } from '../../../components/PageHeader'
import { Button } from '../../../components/ui/Button'
import type { ClassroomSummary } from '../../classrooms/api/classrooms'
import { useImportClassroomDataset, useUploadClassroomDataset } from '../api/classroomImport'
import { fatalChecksOf, missingTableOf, outcomeOf, pathInUpload } from '../importReport'
import { ClassroomAndFileCard, type PackageState } from './ClassroomAndFileCard'
import { ImportActionBar } from './ImportActionBar'
import { ImportResult } from './ImportResult'
import { ImportSteps, type ImportStep } from './ImportSteps'
import { PendingSummaryCard, type PendingStatus } from './PendingSummaryCard'
import './ImportCards.css'

interface ClassroomImportFlowProps {
  classrooms: ClassroomSummary[]
  // Recomeça do zero, e quem monta o fluxo troca a key para ele nascer limpo
  onRestart: () => void
}

export function ClassroomImportFlow({ classrooms, onRestart }: ClassroomImportFlowProps) {
  // Com uma turma só, ela já vem escolhida
  const [classroomId, setClassroomId] = useState<number | null>(() =>
    classrooms.length === 1 ? classrooms[0].id : null,
  )
  const [chosenTable, setChosenTable] = useState<string | null>(null)
  const upload = useUploadClassroomDataset()
  const importDataset = useImportClassroomDataset()

  // O resto se calcula das duas mutações, sem guardar cópia em estado
  const classroom = classrooms.find((candidate) => candidate.id === classroomId)
  const fileName = upload.variables?.file.name ?? ''
  const detected = upload.data
  const mainTable =
    chosenTable ?? (detected?.main_tables.length === 1 ? detected.main_tables[0] : null)
  const report = importDataset.data
  const outcome = report ? outcomeOf(report) : null
  const canProcess =
    classroom != null &&
    detected != null &&
    missingTableOf(detected) == null &&
    mainTable != null &&
    !importDataset.isPending

  function discardFile() {
    upload.reset()
    importDataset.reset()
    setChosenTable(null)
  }

  // O cru do envio fica guardado sob a turma, então trocar de turma descarta o arquivo
  function handleClassroomChange(id: number) {
    setClassroomId(id)
    discardFile()
  }

  function handleFile(file: File) {
    if (classroomId == null) return
    discardFile()
    upload.mutate({ classroomId, file })
  }

  function runImport() {
    if (!canProcess) return
    importDataset.mutate({
      classroom_id: classroom.id,
      raw_dir: detected.raw_dir,
      main_table: mainTable,
    })
  }

  if (report && outcome === 'imported' && classroom && detected && mainTable) {
    return (
      <div className="import-flow">
        <ImportHeader step={3} />
        <ImportResult
          report={report}
          classroomName={classroom.name}
          fileName={fileName}
          mainTable={pathInUpload(mainTable, detected)}
        />
        <ImportActionBar message="Próximo passo: extrair os conceitos de cada exercício.">
          <Button variant="secondary" onClick={onRestart}>
            Importar outros dados
          </Button>
        </ImportActionBar>
      </div>
    )
  }

  const pendingStatus = pendingStatusOf(importDataset, outcome, report)
  return (
    <div className="import-flow">
      <ImportHeader step={pendingStatus.kind === 'waiting' ? 1 : 2} />
      <div className="import-cards">
        <div className="import-cards__main">
          <ClassroomAndFileCard
            classrooms={classrooms}
            classroomId={classroomId}
            onClassroomChange={handleClassroomChange}
            packageState={packageStateOf(upload, fileName)}
            onFile={handleFile}
            onDiscardFile={discardFile}
            mainTable={mainTable}
            onMainTableChange={setChosenTable}
            locked={importDataset.isPending}
          />
        </div>
        <div className="import-cards__side">
          <PendingSummaryCard status={pendingStatus} onRetry={runImport} />
        </div>
      </div>
      <ImportActionBar
        message={
          importDataset.isPending
            ? 'Processando. Não feche esta página.'
            : 'Processar grava os dados na turma escolhida. Leva de alguns segundos a um minuto.'
        }
      >
        <Button
          variant="secondary"
          onClick={() => {
            window.location.hash = '#/classrooms'
          }}
          disabled={importDataset.isPending}
        >
          Cancelar
        </Button>
        <Button variant="primary" onClick={runImport} disabled={!canProcess}>
          {importDataset.isPending ? 'Processando…' : 'Processar dados'}
        </Button>
      </ImportActionBar>
    </div>
  )
}

function ImportHeader({ step }: { step: ImportStep }) {
  return (
    <PageHeader
      title="Importar dados"
      description="Envie um pacote ProgSnap2 para uma das suas turmas."
      action={<ImportSteps current={step} />}
    />
  )
}

type UploadMutation = ReturnType<typeof useUploadClassroomDataset>
type ImportMutation = ReturnType<typeof useImportClassroomDataset>

function packageStateOf(upload: UploadMutation, fileName: string): PackageState {
  if (upload.isPending) return { kind: 'uploading', fileName }
  if (upload.isError) return { kind: 'failed', error: upload.error }
  if (upload.data) return { kind: 'detected', fileName, upload: upload.data }
  return { kind: 'empty' }
}

function pendingStatusOf(
  importDataset: ImportMutation,
  outcome: ReturnType<typeof outcomeOf> | null,
  report: ImportMutation['data'],
): PendingStatus {
  if (importDataset.isPending) return { kind: 'processing' }
  if (importDataset.isError) return { kind: 'failed' }
  if (outcome === 'busy') return { kind: 'busy' }
  if (outcome === 'refused' && report)
    return { kind: 'refused', fatalChecks: fatalChecksOf(report) }
  return { kind: 'waiting' }
}
