import { Check, CircleAlert } from 'lucide-react'

import { Badge } from '../../../components/ui/Badge'
import { Card } from '../../../components/ui/Card'
import { formatCount } from '../../../lib/format'
import type { ClassroomImportReport } from '../api/classroomImport'
import { checkTitle, readinessSentence, warningsOf } from '../importReport'
import './ImportCards.css'

// As quatro contagens na ordem em que a tela as mostra, com a chave que o backend usa
const SUMMARY_NUMBERS = [
  { key: 'n_students', label: 'alunos' },
  { key: 'n_problems', label: 'problemas' },
  { key: 'n_assignments', label: 'exercícios' },
  { key: 'n_submissions', label: 'submissões' },
]

interface ImportResultProps {
  report: ClassroomImportReport
  classroomName: string
  fileName: string
  mainTable: string
}

export function ImportResult({ report, classroomName, fileName, mainTable }: ImportResultProps) {
  return (
    <>
      <div role="status" className="import-banner">
        <Check className="import-banner__icon" size={18} strokeWidth={2.6} aria-hidden="true" />
        <span>
          <strong>
            {fileName} importado em {classroomName}.
          </strong>{' '}
          {readinessSentence(report.per_assignment)}
        </span>
      </div>
      <div className="import-cards import-cards--result">
        <div className="import-cards__main">
          <Card title="Resumo dos dados">
            <div className="summary-numbers">
              {SUMMARY_NUMBERS.map(({ key, label }) => (
                <div key={key}>
                  <div className="summary-numbers__value mono">
                    {formatCount(report.dataset_summary[key] ?? 0)}
                  </div>
                  <div className="summary-numbers__label">{label}</div>
                </div>
              ))}
            </div>
            <table className="assignment-table">
              <thead>
                <tr>
                  <th scope="col">Exercício</th>
                  <th scope="col">Situação</th>
                </tr>
              </thead>
              <tbody>
                {report.per_assignment.map((assignment) => (
                  <tr key={assignment.progsnap_assignment_id}>
                    <td className="assignment-table__name">
                      Assignment {assignment.progsnap_assignment_id}
                    </td>
                    <td>
                      <Badge tone="neutral">
                        {assignment.trainable ? 'Pronto para conceitos' : 'Só estatísticas'}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
        <div className="import-cards__side">
          <ImportedDetailsCard
            report={report}
            classroomName={classroomName}
            fileName={fileName}
            mainTable={mainTable}
          />
        </div>
      </div>
    </>
  )
}

function ImportedDetailsCard({ report, classroomName, fileName, mainTable }: ImportResultProps) {
  const warnings = warningsOf(report)
  return (
    <Card title="O que foi importado">
      <div className="import-card__body">
        <dl className="imported-details">
          <dt>Turma</dt>
          <dd className="imported-details__strong">{classroomName}</dd>
          <dt>Arquivo</dt>
          <dd>{fileName}</dd>
          <dt>Tabela usada</dt>
          <dd className="mono">{mainTable}</dd>
        </dl>
        <div className="import-card__rule" />
        <span className="import-card__section-title">Avisos do processamento</span>
        {warnings.length === 0 ? (
          <p className="pending-intro">Nenhum aviso. O sistema não precisou ajustar nada.</p>
        ) : (
          <ul className="import-warnings">
            {warnings.map((warning) => (
              <li key={`${warning.check}-${warning.message}`} className="import-warnings__item">
                <CircleAlert className="import-warnings__icon" size={17} aria-hidden="true" />
                <div className="import-warnings__text">
                  <span className="import-warnings__title">{checkTitle(warning)}</span>
                  <span>{warning.message}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
        <p className="pending-intro">
          Avisos não impedem a importação. Eles registram o que o sistema ajustou sozinho.
        </p>
      </div>
    </Card>
  )
}
