import { Check } from 'lucide-react'

import './ImportSteps.css'

export type ImportStep = 1 | 2 | 3

const STEPS: { step: ImportStep; label: string }[] = [
  { step: 1, label: 'Turma e arquivo' },
  { step: 2, label: 'Processar' },
  { step: 3, label: 'Conferir' },
]

export function ImportSteps({ current }: { current: ImportStep }) {
  return (
    <ol aria-label="Etapas da importação" className="import-steps">
      {STEPS.map(({ step, label }) => (
        <li
          key={step}
          className={`import-steps__item import-steps__item--${stateOf(step, current)}`}
          aria-current={step === current ? 'step' : undefined}
        >
          <span className="import-steps__marker">
            {step < current ? <Check size={12} strokeWidth={3} aria-hidden="true" /> : step}
          </span>
          <span className="import-steps__label">{label}</span>
        </li>
      ))}
    </ol>
  )
}

function stateOf(step: ImportStep, current: ImportStep) {
  if (step < current) return 'done'
  return step === current ? 'current' : 'todo'
}
