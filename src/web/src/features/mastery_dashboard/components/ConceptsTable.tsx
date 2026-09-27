import { useState } from 'react'

import { Histogram } from '../../../components/ui/Histogram'
import { InfoHint } from '../../../components/ui/InfoHint'
import { RatioBar } from '../../../components/ui/RatioBar'
import { SortableHeader } from '../../../components/ui/SortableHeader'
import { formatCount } from '../../../lib/format'
import { DISTRIBUTION_HINT, MASTERY_HINT, type ConceptRow } from '../dashboard'
import { sortRows, toggleSort, type SortState } from '../sorting'
import { ConceptRecurrence } from './ConceptRecurrence'
import { EstimatedMark } from './EstimatedMark'
import './AnalysisTable.css'

type SortKey = 'kc_name' | 'success_rate' | 'runs' | 'recurrence' | 'mean_mastery'

interface ConceptsTableProps {
  concepts: ConceptRow[]
  withModel: boolean
}

// Um conceito por linha, a taxa somando as execuções dos problemas que o exigem
export function ConceptsTable({ concepts, withModel }: ConceptsTableProps) {
  const [sort, setSort] = useState<SortState<SortKey>>({ key: 'success_rate', direction: 'asc' })
  const rows = sortRows(concepts, sort)
  const header = (
    key: SortKey,
    label: React.ReactNode,
    align: 'start' | 'center' | 'end',
    hint?: React.ReactNode,
  ) => (
    <SortableHeader
      align={align}
      direction={sort.key === key ? sort.direction : null}
      onSort={() => setSort(toggleSort(sort, key))}
      hint={hint}
    >
      {label}
    </SortableHeader>
  )
  return (
    <div className="analysis-table__scroll">
      <table className="analysis-table" aria-label="Conceitos">
        <thead>
          <tr>
            {header('kc_name', 'Conceito', 'start')}
            {header('success_rate', 'Taxa de acerto', 'start')}
            {header('runs', 'Execuções', 'center')}
            {header('recurrence', 'Recorrência', 'center')}
            {withModel
              ? header(
                  'mean_mastery',
                  <>
                    <EstimatedMark />
                    Domínio
                  </>,
                  'start',
                  <InfoHint text={MASTERY_HINT} />,
                )
              : null}
            {withModel ? (
              <th scope="col">
                <EstimatedMark />
                Distribuição
                <InfoHint text={DISTRIBUTION_HINT} />
              </th>
            ) : null}
          </tr>
        </thead>
        <tbody>
          {rows.map((kc) => (
            <tr key={kc.kc_id}>
              <td className="analysis-table__name">{kc.kc_name}</td>
              <td className="analysis-table__bar">
                <RatioBar
                  value={kc.success_rate}
                  tone="observed"
                  label={`Taxa de acerto em ${kc.kc_name}`}
                />
              </td>
              <td className="analysis-table__num">{formatCount(kc.runs)}</td>
              <td className="analysis-table__num">
                <ConceptRecurrence problemIds={kc.problem_ids} />
              </td>
              {withModel ? (
                <td className="analysis-table__bar">
                  {kc.mean_mastery == null ? (
                    <span className="analysis-table__missing">—</span>
                  ) : (
                    <RatioBar
                      value={kc.mean_mastery}
                      tone="predicted"
                      label={`Domínio estimado em ${kc.kc_name}`}
                    />
                  )}
                </td>
              ) : null}
              {withModel ? (
                <td className="analysis-table__hist">
                  {kc.histogram ? (
                    <Histogram
                      bins={kc.histogram}
                      unit="alunos"
                      axis={false}
                      label={`Distribuição dos alunos em ${kc.kc_name}`}
                    />
                  ) : (
                    <span className="analysis-table__missing">—</span>
                  )}
                </td>
              ) : null}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
