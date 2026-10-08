import { formatPercent } from '../../lib/format'

import './RatioBar.css'

// Cada tom é uma família de dado, o observado em cinza e o previsto em azul, nunca as duas juntas
type RatioBarTone = 'observed' | 'predicted'

interface RatioBarProps {
  // Uma fração de 0 a 1, sempre na régua inteira, para o eixo nunca enganar
  value: number
  tone: RatioBarTone
  label: string
}

export function RatioBar({ value, tone, label }: RatioBarProps) {
  const percent = formatPercent(value)
  return (
    <div className="ratio-bar" role="img" aria-label={`${label} ${percent}`}>
      <div className="ratio-bar__track">
        <div
          className={`ratio-bar__fill ratio-bar__fill--${tone}`}
          style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }}
        />
      </div>
      <span className="ratio-bar__value num">{percent}</span>
    </div>
  )
}
