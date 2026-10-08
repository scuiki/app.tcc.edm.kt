import { Check, FileText, LoaderCircle, X } from 'lucide-react'

import { FileDropZone } from '../../../components/FileDropZone'
import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { SelectField } from '../../../components/ui/SelectField'
import type { ClassroomSummary } from '../../classrooms/api/classrooms'
import { UploadTooLargeError, type DetectedUpload } from '../api/classroomImport'
import { missingTableOf, pathInUpload } from '../importReport'
import { OutcomeMessage } from '../../../components/OutcomeMessage'
import './ImportCards.css'
import './ClassroomAndFileCard.css'

// O que a área do pacote mostra, um estado de cada vez
export type PackageState =
  | { kind: 'empty' }
  | { kind: 'uploading'; fileName: string }
  | { kind: 'failed'; error: Error }
  | { kind: 'detected'; fileName: string; upload: DetectedUpload }

interface ClassroomAndFileCardProps {
  classrooms: ClassroomSummary[]
  classroomId: number | null
  onClassroomChange: (classroomId: number) => void
  packageState: PackageState
  onFile: (file: File) => void
  onDiscardFile: () => void
  mainTable: string | null
  onMainTableChange: (path: string) => void
  // Travado enquanto processa, para o professor não trocar o que já foi mandado
  locked: boolean
}

export function ClassroomAndFileCard({
  classrooms,
  classroomId,
  onClassroomChange,
  packageState,
  onFile,
  onDiscardFile,
  mainTable,
  onMainTableChange,
  locked,
}: ClassroomAndFileCardProps) {
  const classroom = classrooms.find((candidate) => candidate.id === classroomId)
  return (
    <Card title="Turma e arquivo">
      <div className="import-card__body">
        <SelectField
          label="Turma"
          required
          placeholder="Escolha a turma"
          value={classroomId == null ? '' : String(classroomId)}
          options={classrooms.map(({ id, name }) => ({ value: String(id), label: name }))}
          onChange={(value) => onClassroomChange(Number(value))}
          disabled={locked || packageState.kind === 'uploading'}
          hint={
            <>
              Não encontrou a turma? Crie em <a href="#/classrooms">Nova turma</a>.
            </>
          }
        />
        {classroom && classroom.status !== 'awaiting_data' ? (
          <p className="import-card__note">
            Esta turma já tem dados. Um novo envio cria exercícios novos, mesmo que repitam os que
            já existem.
          </p>
        ) : null}
        <div className="import-card__package">
          <span className="import-card__label">Pacote</span>
          {packageState.kind === 'empty' ? (
            <FileDropZone
              onFile={onFile}
              title="Arraste o arquivo .zip aqui"
              hint={
                classroomId == null
                  ? 'Escolha a turma antes do arquivo'
                  : 'ou clique para escolher no computador'
              }
              detail="ProgSnap2 v6 · até 512 MB"
              accept=".zip,application/zip"
              disabled={classroomId == null}
            />
          ) : null}
          {packageState.kind === 'uploading' ? (
            <UploadingFile fileName={packageState.fileName} />
          ) : null}
          {packageState.kind === 'failed' ? (
            <UploadFailure error={packageState.error} onRetry={onDiscardFile} />
          ) : null}
          {packageState.kind === 'detected' ? (
            <DetectedPackage
              fileName={packageState.fileName}
              upload={packageState.upload}
              onDiscardFile={onDiscardFile}
              mainTable={mainTable}
              onMainTableChange={onMainTableChange}
              locked={locked}
            />
          ) : null}
        </div>
      </div>
    </Card>
  )
}

function UploadingFile({ fileName }: { fileName: string }) {
  return (
    <div className="package-file" role="status">
      <LoaderCircle className="package-file__spinner" size={17} aria-hidden="true" />
      <span className="package-file__name">{fileName}</span>
      <span className="t-support">Enviando e lendo o pacote…</span>
    </div>
  )
}

function UploadFailure({ error, onRetry }: { error: Error; onRetry: () => void }) {
  const tooLarge = error instanceof UploadTooLargeError
  return (
    <div className="package-refusal">
      <OutcomeMessage
        tone="danger"
        title={tooLarge ? 'O arquivo passa de 512 MB' : 'Não foi possível abrir o arquivo'}
      >
        {tooLarge
          ? 'O limite de envio é 512 MB. Confira se o arquivo escolhido é o pacote da turma.'
          : 'O sistema espera um pacote .zip exportado no formato ProgSnap2. Confira se o arquivo não foi renomeado ou corrompido no download.'}
      </OutcomeMessage>
      <Button variant="primary" onClick={onRetry}>
        Escolher outro arquivo
      </Button>
    </div>
  )
}

interface DetectedPackageProps {
  fileName: string
  upload: DetectedUpload
  onDiscardFile: () => void
  mainTable: string | null
  onMainTableChange: (path: string) => void
  locked: boolean
}

function DetectedPackage({
  fileName,
  upload,
  onDiscardFile,
  mainTable,
  onMainTableChange,
  locked,
}: DetectedPackageProps) {
  const missing = missingTableOf(upload)
  return (
    <>
      <div className="package-file">
        <FileText className="package-file__icon" size={17} aria-hidden="true" />
        <span className="package-file__name">{fileName}</span>
        <Button variant="secondary" onClick={onDiscardFile} disabled={locked}>
          Trocar
        </Button>
      </div>
      <div className="import-card__rule" />
      <span className="import-card__section-title">O que veio no pacote</span>
      <ul className="package-contents">
        {upload.main_tables.map((path) => (
          <PackageItem key={path} found name={pathInUpload(path, upload)} role="eventos" />
        ))}
        {upload.main_tables.length === 0 ? (
          <PackageItem found={false} name="MainTable.csv" role="não encontrado" />
        ) : null}
        <PackageItem
          found={upload.code_snapshots != null}
          name={
            upload.code_snapshots ? pathInUpload(upload.code_snapshots, upload) : 'CodeStates.csv'
          }
          role={upload.code_snapshots ? 'código dos alunos' : 'não encontrado'}
        />
      </ul>
      {missing ? (
        <MissingTableRefusal missing={missing} onRetry={onDiscardFile} />
      ) : (
        <MainTableChoice
          upload={upload}
          mainTable={mainTable}
          onMainTableChange={onMainTableChange}
          locked={locked}
        />
      )}
    </>
  )
}

function PackageItem({ found, name, role }: { found: boolean; name: string; role: string }) {
  const Icon = found ? Check : X
  return (
    <li className={`package-contents__item${found ? '' : ' package-contents__item--missing'}`}>
      <Icon className="package-contents__icon" size={15} strokeWidth={2.6} aria-hidden="true" />
      <span className="num package-contents__name">{name}</span>
      <span className="t-support">{role}</span>
    </li>
  )
}

const MISSING_TABLE_COPY = {
  main_table: {
    title: 'O pacote não tem MainTable.csv',
    text: 'Sem a tabela de eventos não há tentativas para importar. Confira se o .zip foi exportado completo.',
  },
  code_snapshots: {
    title: 'O pacote não tem CodeStates.csv',
    text: 'Sem o código dos alunos não há como extrair conceitos nem treinar o modelo. Confira se o .zip foi exportado completo.',
  },
}

function MissingTableRefusal({
  missing,
  onRetry,
}: {
  missing: keyof typeof MISSING_TABLE_COPY
  onRetry: () => void
}) {
  const copy = MISSING_TABLE_COPY[missing]
  return (
    <div className="package-refusal">
      <OutcomeMessage tone="danger" title={copy.title}>
        {copy.text}
      </OutcomeMessage>
      <Button variant="primary" onClick={onRetry}>
        Escolher outro arquivo
      </Button>
    </div>
  )
}

interface MainTableChoiceProps {
  upload: DetectedUpload
  mainTable: string | null
  onMainTableChange: (path: string) => void
  locked: boolean
}

// Com uma tabela só não há o que escolher, e com várias o professor escolhe, sem adivinhação
function MainTableChoice({ upload, mainTable, onMainTableChange, locked }: MainTableChoiceProps) {
  if (upload.main_tables.length === 1) {
    return (
      <p className="import-card__note">
        Uma tabela de eventos encontrada. Quando o pacote traz mais de uma, você escolhe qual usar
        aqui.
      </p>
    )
  }
  return (
    <fieldset className="table-choice">
      <legend className="import-card__label">
        O pacote traz {upload.main_tables.length} tabelas de eventos. Escolha qual usar.
      </legend>
      {upload.main_tables.map((path) => (
        <label key={path} className="table-choice__option">
          <input
            type="radio"
            name="main-table"
            value={path}
            checked={mainTable === path}
            disabled={locked}
            onChange={() => onMainTableChange(path)}
          />
          <span className="num">{pathInUpload(path, upload)}</span>
        </label>
      ))}
    </fieldset>
  )
}
