import { QueryStates } from '../../../components/states/states'
import { Button } from '../../../components/ui/Button'
import { Dialog, DialogBody, DialogFooter } from '../../../components/ui/Dialog'
import { InfoHint } from '../../../components/ui/InfoHint'
import { RatioBar } from '../../../components/ui/RatioBar'
import { formatCount, formatPercent } from '../../../lib/format'
import { useStudent } from '../api/masteryDashboard'
import { MASTERY_HINT } from '../dashboard'
import { EstimatedMark } from './EstimatedMark'
import './StudentDialog.css'

interface StudentDialogProps {
  assignmentId: number
  problemCount: number
  // Null fechado; o detalhe só é buscado com o diálogo aberto
  studentId: string | null
  onClose: () => void
}

export function StudentDialog({
  assignmentId,
  problemCount,
  studentId,
  onClose,
}: StudentDialogProps) {
  return (
    <Dialog open={studentId != null} onClose={onClose} title={`Aluno ${studentId ?? ''}`}>
      {studentId != null ? (
        <StudentDetail
          assignmentId={assignmentId}
          problemCount={problemCount}
          studentId={studentId}
        />
      ) : null}
      <DialogFooter>
        <Button variant="secondary" onClick={onClose}>
          Fechar
        </Button>
      </DialogFooter>
    </Dialog>
  )
}

function StudentDetail({
  assignmentId,
  problemCount,
  studentId,
}: {
  assignmentId: number
  problemCount: number
  studentId: string
}) {
  const query = useStudent(assignmentId, studentId)
  return (
    <DialogBody>
      <QueryStates query={query} loadingLabel="Carregando o aluno…">
        {(student) => (
          <div className="student-dialog">
            <dl className="student-dialog__tiles">
              <div>
                <dt>
                  <EstimatedMark />
                  Domínio
                  <InfoHint text={MASTERY_HINT} />
                </dt>
                <dd className="num">{formatPercent(student.mean_mastery)}</dd>
              </div>
              <div>
                <dt>Completou</dt>
                <dd className="num">
                  {student.completed} <span className="student-dialog__sub">de {problemCount}</span>
                </dd>
              </div>
              <div>
                <dt>Tentou</dt>
                <dd className="num">
                  {student.attempted} <span className="student-dialog__sub">de {problemCount}</span>
                </dd>
              </div>
              <div>
                <dt>Execuções</dt>
                <dd className="num">{formatCount(student.runs)}</dd>
              </div>
              <div>
                <dt>Erros de compilação</dt>
                <dd className="num">{formatCount(student.compile_errors)}</dd>
              </div>
            </dl>
            <section className="student-dialog__section" aria-label="Domínio por conceito">
              <h3 className="student-dialog__title">
                <EstimatedMark />
                Domínio por conceito
              </h3>
              <ul className="student-dialog__list">
                {student.knowledge_components.map((kc) => (
                  <li key={kc.kc_id} className="student-dialog__row">
                    <span className="student-dialog__label" title={kc.kc_name}>
                      {kc.kc_name}
                    </span>
                    <RatioBar value={kc.mastery} tone="predicted" label={kc.kc_name} />
                  </li>
                ))}
              </ul>
            </section>
            <section className="student-dialog__section" aria-label="Domínio por problema">
              <h3 className="student-dialog__title">
                <EstimatedMark />
                Domínio por problema
              </h3>
              <ul className="student-dialog__list">
                {student.problems.map((problem) => (
                  <li key={problem.problem_id} className="student-dialog__row">
                    <span className="student-dialog__label">Problema {problem.problem_id}</span>
                    <RatioBar
                      value={problem.mastery}
                      tone="predicted"
                      label={`Problema ${problem.problem_id}`}
                    />
                  </li>
                ))}
              </ul>
            </section>
          </div>
        )}
      </QueryStates>
    </DialogBody>
  )
}
