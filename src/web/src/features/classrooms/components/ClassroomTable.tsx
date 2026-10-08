import { useState } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { Pencil, Plus, Trash2, Users } from 'lucide-react'

import { EmptyState, QueryStates } from '../../../components/states/states'
import { Button, IconButton } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { ColumnHeader, DataTable } from '../../../components/ui/DataTable'
import { SearchField } from '../../../components/ui/SearchField'
import { formatCount, formatDate } from '../../../lib/format'
import { classroomPath } from '../../../lib/paths'
import type { ClassroomSummary } from '../api/classrooms'
import { ClassroomStatusBadge } from './ClassroomStatusBadge'
import './ClassroomTable.css'

// Sem acento e sem caixa, para "algoritmos" achar "Algoritmos I"
function normalize(text: string) {
  return text
    .normalize('NFD')
    .replace(/\p{Diacritic}/gu, '')
    .toLowerCase()
}

function matchesSearch(classroom: ClassroomSummary, search: string) {
  return normalize(classroom.name).includes(normalize(search.trim()))
}

interface ClassroomTableProps {
  query: UseQueryResult<{ classrooms: ClassroomSummary[] }>
  onCreate: () => void
  onRename: (classroomId: number) => void
  onRemove: (classroomId: number) => void
}

export function ClassroomTable({ query, onCreate, onRename, onRemove }: ClassroomTableProps) {
  const [search, setSearch] = useState('')
  const classrooms = query.data?.classrooms ?? []
  const visible = classrooms.filter((classroom) => matchesSearch(classroom, search))
  const hasClassrooms = classrooms.length > 0

  return (
    <Card
      title="Turmas"
      actions={
        hasClassrooms ? (
          <SearchField label="Buscar turma" value={search} onChange={setSearch} />
        ) : null
      }
      footer={hasClassrooms ? `${classrooms.length} ${pluralize(classrooms.length)}` : null}
    >
      <QueryStates
        query={query}
        loadingLabel="Carregando turmas…"
        isEmpty={(data) => data.classrooms.length === 0}
        empty={
          <EmptyState
            icon={Users}
            title="Nenhuma turma ainda"
            text="Cadastre a primeira turma. Depois você importa os dados ProgSnap2 dela e segue para a extração de conceitos."
            action={
              <Button variant="primary" icon={Plus} onClick={onCreate}>
                Nova turma
              </Button>
            }
          />
        }
      >
        {() => (
          <DataTable label="Turmas">
            <thead>
              <tr>
                <ColumnHeader label="Turma" />
                <ColumnHeader label="Problemas" />
                <ColumnHeader label="Alunos" />
                <ColumnHeader label="Criada em" />
                <ColumnHeader label="Situação" />
                <th scope="col" className="data-table__actions">
                  <span className="visually-hidden">Ações</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {visible.map((classroom) => (
                <ClassroomRow
                  key={classroom.id}
                  classroom={classroom}
                  onRename={onRename}
                  onRemove={onRemove}
                />
              ))}
              {visible.length === 0 ? (
                <tr>
                  <td colSpan={6} className="classroom-table__no-match">
                    Nenhuma turma com esse nome.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </DataTable>
        )}
      </QueryStates>
    </Card>
  )
}

function pluralize(count: number) {
  return count === 1 ? 'turma' : 'turmas'
}

interface ClassroomRowProps {
  classroom: ClassroomSummary
  onRename: (classroomId: number) => void
  onRemove: (classroomId: number) => void
}

function ClassroomRow({ classroom, onRename, onRemove }: ClassroomRowProps) {
  return (
    <tr>
      <td className="data-table__name">
        <a href={`#${classroomPath(classroom.id)}`}>{classroom.name}</a>
      </td>
      <CountCell value={classroom.problem_count} />
      <CountCell value={classroom.student_count} />
      <td className="data-table__num">{formatDate(classroom.created_at)}</td>
      <td className="data-table__num">
        <ClassroomStatusBadge status={classroom.status} />
      </td>
      <td className="data-table__actions">
        <IconButton
          icon={Pencil}
          label={`Renomear ${classroom.name}`}
          onClick={() => onRename(classroom.id)}
        />
        <IconButton
          icon={Trash2}
          label={`Excluir ${classroom.name}`}
          onClick={() => onRemove(classroom.id)}
        />
      </td>
    </tr>
  )
}

// Traço no lugar de zero, porque a turma sem dados ainda não tem o que contar
function CountCell({ value }: { value: number }) {
  return (
    <td className="data-table__num">
      {value === 0 ? <span className="data-table__missing">—</span> : formatCount(value)}
    </td>
  )
}
