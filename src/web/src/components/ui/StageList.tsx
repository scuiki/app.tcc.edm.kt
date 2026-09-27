import { Check, Circle, LoaderCircle } from 'lucide-react'

import './StageList.css'

export type StageState = 'done' | 'current' | 'todo'

export interface StageItem {
  key: string
  label: string
  state: StageState
  // O andamento do estágio atual, como "3 de 8" ou "época 12 de 40"
  progress?: string | null
}

const STAGE_ICON: Record<StageState, typeof Check> = {
  done: Check,
  current: LoaderCircle,
  todo: Circle,
}

// Os estágios de um job longo, o atual girando e marcado como o passo corrente
export function StageList({ items }: { items: StageItem[] }) {
  return (
    <ol className="stage-list">
      {items.map(({ key, label, state, progress }) => {
        const Icon = STAGE_ICON[state]
        return (
          <li
            key={key}
            className={`stage-list__item stage-list__item--${state}`}
            aria-current={state === 'current' ? 'step' : undefined}
          >
            <Icon className="stage-list__icon" size={17} aria-hidden="true" />
            <span className="stage-list__label">{label}</span>
            {state === 'current' && progress ? (
              <span className="stage-list__progress mono">{progress}</span>
            ) : null}
          </li>
        )
      })}
    </ol>
  )
}
