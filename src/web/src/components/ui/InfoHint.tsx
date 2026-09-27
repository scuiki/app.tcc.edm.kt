import { CircleAlert } from 'lucide-react'

import { Tooltip } from './Tooltip'
import './InfoHint.css'

// O "!" ao lado de um termo, com a explicação no hover e no leitor de tela
export function InfoHint({ text }: { text: string }) {
  return (
    <Tooltip text={text}>
      <button type="button" className="info-hint" aria-label={text}>
        <CircleAlert size={14} aria-hidden="true" />
      </button>
    </Tooltip>
  )
}
