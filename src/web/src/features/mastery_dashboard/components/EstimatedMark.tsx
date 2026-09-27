import { Brain } from 'lucide-react'

import { Tooltip } from '../../../components/ui/Tooltip'
import { ESTIMATED_HINT } from '../dashboard'
import './EstimatedMark.css'

// O cérebro ao lado de toda coluna que vem do modelo; o hover diz que o dado é estimado
export function EstimatedMark() {
  return (
    <Tooltip text={ESTIMATED_HINT}>
      <span className="estimated-mark" role="img" aria-label={ESTIMATED_HINT}>
        <Brain size={13} aria-hidden="true" />
      </span>
    </Tooltip>
  )
}
