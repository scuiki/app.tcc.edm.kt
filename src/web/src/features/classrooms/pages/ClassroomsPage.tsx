import { useState } from 'react'
import { Plus } from 'lucide-react'

import { PageHeader } from '../../../components/PageHeader'
import { Button } from '../../../components/ui/Button'
import { useClassrooms } from '../api/classrooms'
import { ClassroomNameDialog } from '../components/ClassroomNameDialog'
import { ClassroomTable } from '../components/ClassroomTable'
import { RecentActivityCard } from '../components/RecentActivityCard'
import { RemoveClassroomDialog } from '../components/RemoveClassroomDialog'
import './ClassroomsPage.css'

// Um diálogo por vez, e a turma pelo id, para nunca guardar uma cópia que envelhece
type DialogState =
  | { kind: 'closed' }
  | { kind: 'create' }
  | { kind: 'rename'; classroomId: number }
  | { kind: 'remove'; classroomId: number }

const CLOSED: DialogState = { kind: 'closed' }

export function ClassroomsPage() {
  const query = useClassrooms()
  const [dialog, setDialog] = useState<DialogState>(CLOSED)
  const classrooms = query.data?.classrooms ?? []
  const target =
    dialog.kind === 'rename' || dialog.kind === 'remove'
      ? classrooms.find((classroom) => classroom.id === dialog.classroomId)
      : undefined
  const close = () => setDialog(CLOSED)

  return (
    <>
      <PageHeader
        title="Minhas turmas"
        description="Crie e gerencie suas turmas"
        action={
          <Button variant="primary" icon={Plus} onClick={() => setDialog({ kind: 'create' })}>
            Nova turma
          </Button>
        }
      />
      <div className="classrooms-layout">
        <div className="classrooms-layout__main">
          <ClassroomTable
            query={query}
            onCreate={() => setDialog({ kind: 'create' })}
            onRename={(classroomId) => setDialog({ kind: 'rename', classroomId })}
            onRemove={(classroomId) => setDialog({ kind: 'remove', classroomId })}
          />
        </div>
        {classrooms.length > 0 ? (
          <div className="classrooms-layout__side">
            <RecentActivityCard classrooms={classrooms} />
          </div>
        ) : null}
      </div>
      <ClassroomNameDialog
        open={dialog.kind === 'create' || (dialog.kind === 'rename' && target != null)}
        classroom={dialog.kind === 'rename' ? target : undefined}
        onClose={close}
      />
      <RemoveClassroomDialog
        classroom={dialog.kind === 'remove' ? target : undefined}
        onClose={close}
      />
    </>
  )
}
