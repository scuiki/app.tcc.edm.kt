import { Fragment, type ReactNode } from 'react'
import { CircleAlert } from 'lucide-react'

import './FactsLine.css'

export interface Fact {
  // O texto do fato, com os números já marcados em `.num`
  content: ReactNode
  // O fato que pede atenção, em vermelho e com o !
  alert?: boolean
}

// A vírgula vai como texto, porque o leitor de tela e o jsdom não leem pseudo-elemento
export function FactsLine({ facts }: { facts: Fact[] }) {
  return (
    <p className="facts-line">
      {facts.map((fact, index) => (
        <Fragment key={index}>
          {index > 0 ? ', ' : null}
          {fact.alert ? (
            <span className="facts-line__item facts-line__item--alert">
              <CircleAlert size={14} aria-hidden="true" />
              <span>{fact.content}</span>
            </span>
          ) : (
            <span className="facts-line__item">{fact.content}</span>
          )}
        </Fragment>
      ))}
    </p>
  )
}
