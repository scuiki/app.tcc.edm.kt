import { useState } from 'react'
import { Users } from 'lucide-react'

import { PageHeader } from '../../../components/PageHeader'
import { EmptyState, QueryStates } from '../../../components/states/states'
import { Card } from '../../../components/ui/Card'
import { useClassrooms } from '../../classrooms/api/classrooms'
import { ClassroomImportFlow } from '../components/ClassroomImportFlow'

export function ClassroomImportPage() {
  // Cada tentativa é uma key, e trocar a key faz o fluxo nascer limpo, sem reset à mão
  const [attempt, setAttempt] = useState(0)
  const query = useClassrooms()
  const classrooms = query.data?.classrooms ?? []

  if (classrooms.length > 0) {
    return (
      <ClassroomImportFlow
        key={attempt}
        classrooms={classrooms}
        onRestart={() => setAttempt((current) => current + 1)}
      />
    )
  }
  return (
    <>
      <PageHeader
        title="Importar dados"
        description="Envie um pacote ProgSnap2 para uma das suas turmas."
      />
      <Card title="Turma e arquivo">
        <QueryStates
          query={query}
          loadingLabel="Carregando turmas…"
          isEmpty={(data) => data.classrooms.length === 0}
          empty={
            <EmptyState
              icon={Users}
              title="Nenhuma turma ainda"
              text="Os dados são importados para uma turma. Crie a turma primeiro e volte aqui."
              action={<a href="#/classrooms">Ir para Turmas</a>}
            />
          }
        >
          {() => null}
        </QueryStates>
      </Card>
    </>
  )
}
