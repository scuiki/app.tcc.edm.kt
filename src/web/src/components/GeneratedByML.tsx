import { Brain } from 'lucide-react'

import { Tooltip } from './ui/Tooltip'
import './GeneratedByML.css'

const HINT = 'Dado estimado por aprendizado de máquina'

// O cérebro antes do rótulo de toda coluna que vem do Code-DKT, com a origem do dado no hover
export function GeneratedByML() {
  return (
    <Tooltip text={HINT}>
      <span className="generated-by-ml" role="img" aria-label={HINT}>
        <Brain size={13} aria-hidden="true" />
      </span>
    </Tooltip>
  )
}
