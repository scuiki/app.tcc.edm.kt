import { Button } from '../../../components/ui/Button'
import { Card } from '../../../components/ui/Card'
import { assignmentPath } from '../../../lib/paths'
import './AssignmentStateCards.css'

// O exercício não treina, as primeiras tentativas têm uma classe só e o AUC é indefinido
export function NotTrainableCard() {
  return (
    <Card title="Modelo">
      <p className="state-card__text">
        Este exercício não treina um modelo. As primeiras tentativas dos alunos têm uma classe só,
        então não há o que o modelo aprender. Fica o que aconteceu nas execuções.
      </p>
    </Card>
  )
}

export function NoApprovedConceptsCard({
  classroomId,
  assignmentId,
}: {
  classroomId: number
  assignmentId: number
}) {
  return (
    <Card title="Modelo">
      <p className="state-card__text">
        Sem conceitos aprovados. Extraia e aprove os conceitos deste exercício para treinar o modelo
        e ver o domínio da turma.
      </p>
      <p className="state-card__action">
        <a href={`#${assignmentPath(classroomId, assignmentId, 'knowledge-components')}`}>
          Ir para Conceitos
        </a>
      </p>
    </Card>
  )
}

export function TrainModelCard({ onTrain }: { onTrain: () => void }) {
  return (
    <Card title="Modelo">
      <div className="state-card__row">
        <p className="state-card__text">
          Conceitos aprovados, modelo ainda não treinado. O treino leva alguns minutos na GPU e as
          colunas estimadas aparecem aqui em seguida.
        </p>
        <Button variant="primary" onClick={onTrain}>
          Treinar modelo
        </Button>
      </div>
    </Card>
  )
}
