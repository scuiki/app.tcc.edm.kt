import { Sparkles } from 'lucide-react'

import { Tooltip } from './ui/Tooltip'
import './GeneratedByLLM.css'

const HINT = 'Gerado pelo modelo de linguagem'

// O ícone acompanha o círculo de cada lugar, de 24px no título a 16px na aba da solução
const ICON_SIZE = { text: 14, title: 16, label: 12, tab: 10 } as const

interface GeneratedByLLMProps {
  // No fim do texto, no título, antes do rótulo de seção ou na aba da solução com o trecho
  variant?: keyof typeof ICON_SIZE
}

// As estrelas no que o modelo de linguagem escreveu, com a origem do texto no hover
export function GeneratedByLLM({ variant = 'text' }: GeneratedByLLMProps) {
  return (
    <Tooltip text={HINT}>
      <span
        className={`generated-by-llm generated-by-llm--${variant}`}
        role="img"
        aria-label={HINT}
      >
        <Sparkles size={ICON_SIZE[variant]} aria-hidden="true" />
      </span>
    </Tooltip>
  )
}
