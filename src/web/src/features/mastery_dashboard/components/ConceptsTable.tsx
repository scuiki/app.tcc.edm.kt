import { useState, type ReactNode } from 'react'

import { GeneratedByML } from '../../../components/GeneratedByML'
import { ColumnHeader, DataTable } from '../../../components/ui/DataTable'
import { Histogram } from '../../../components/ui/Histogram'
import { InfoHint } from '../../../components/ui/InfoHint'
import { RatioBar } from '../../../components/ui/RatioBar'
import { SortableHeader } from '../../../components/ui/SortableHeader'
import { formatCount } from '../../../lib/format'
import { ANALYSIS_MIN_WIDTH, DISTRIBUTION_HINT, MASTERY_HINT, type ConceptRow } from '../dashboard'
import { sortRows, toggleSort, type SortState } from '../sorting'
import { ConceptRecurrence } from './ConceptRecurrence'
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
  const header = (key: SortKey, label: string, leading?: ReactNode, hint?: ReactNode) => (
    <SortableHeader
      label={label}
      direction={sort.key === key ? sort.direction : null}
      onSort={() => setSort(toggleSort(sort, key))}
      leading={leading}
      hint={hint}
    />
  )
  return (
    <DataTable label="Conceitos" minWidth={ANALYSIS_MIN_WIDTH}>
      <thead>
        <tr>
          {header('kc_name', 'Conceito')}
          {header('success_rate', 'Taxa de acerto')}
          {header('runs', 'Execuções')}
          {header('recurrence', 'Recorrência')}
          {withModel
            ? header('mean_mastery', 'Domínio', <GeneratedByML />, <InfoHint text={MASTERY_HINT} />)
            : null}
          {withModel ? (
            <ColumnHeader
              label="Distribuição"
              leading={<GeneratedByML />}
              hint={<InfoHint text={DISTRIBUTION_HINT} />}
            />
          ) : null}
        </tr>
      </thead>
      <tbody>
        {rows.map((kc) => (
          <tr key={kc.kc_id}>
            <td className="data-table__name">{kc.kc_name}</td>
            <td>
              <RatioBar
                value={kc.success_rate}
                tone="observed"
                label={`Taxa de acerto em ${kc.kc_name}`}
              />
            </td>
            <td className="data-table__num">{formatCount(kc.runs)}</td>
            <td className="data-table__num">
              <ConceptRecurrence problemIds={kc.problem_ids} />
            </td>
            {withModel ? (
              <td>
                {kc.mean_mastery == null ? (
                  <span className="data-table__missing">—</span>
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
              <td>
                {kc.histogram ? (
                  <Histogram
                    bins={kc.histogram}
                    unit="alunos"
                    label={`Distribuição dos alunos em ${kc.kc_name}`}
                  />
                ) : (
                  <span className="data-table__missing">—</span>
                )}
              </td>
            ) : null}
          </tr>
        ))}
      </tbody>
    </DataTable>
  )
}
