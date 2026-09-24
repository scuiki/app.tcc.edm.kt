import { useState } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { Pencil, Plus, Trash2, Users } from 'lucide-react'

import { EmptyState, QueryStates } from '../../../components/states/states'
import { Button, IconButton } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { SearchField } from '../../../components/ui/SearchField'
import { formatCount, formatDate } from '../../../lib/format'
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
            text="Cadastre a primeira turma. Depois você importa o dataset ProgSnap2 dela e segue para a extração de conceitos."
            action={
              <Button variant="primary" icon={Plus} onClick={onCreate}>
                Nova turma
              </Button>
            }
          />
        }
      >
        {() => (
          <div className="classroom-table__scroll">
            <table className="classroom-table">
              <thead>
                <tr>
                  <th scope="col">Turma</th>
                  <th scope="col" className="classroom-table__number">
                    Problemas
                  </th>
                  <th scope="col" className="classroom-table__number">
                    Alunos
                  </th>
                  <th scope="col">Criada em</th>
                  <th scope="col">Situação</th>
                  <th scope="col">
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
            </table>
          </div>
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
      <td className="classroom-table__name">{classroom.name}</td>
      <CountCell value={classroom.problem_count} />
      <CountCell value={classroom.student_count} />
      <td className="mono classroom-table__date">{formatDate(classroom.created_at)}</td>
      <td>
        <ClassroomStatusBadge status={classroom.status} />
      </td>
      <td className="classroom-table__actions">
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
    <td className="mono classroom-table__number">
      {value === 0 ? <span className="classroom-table__missing">—</span> : formatCount(value)}
    </td>
  )
}
