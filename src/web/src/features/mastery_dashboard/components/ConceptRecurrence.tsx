import { useState } from 'react'
import { TriangleAlert } from 'lucide-react'

import { Tooltip } from '../../../components/ui/Tooltip'
import { listProblemIds, problemCount } from '../dashboard'
import './ConceptRecurrence.css'

// Em quantos problemas o conceito aparece; o clique lista quais, e um só é evidência fraca
export function ConceptRecurrence({ problemIds }: { problemIds: number[] }) {
  const [isOpen, setIsOpen] = useState(false)
  const weak = problemIds.length === 1
  const title = weak
    ? `Só o problema ${problemIds[0]}. O valor deste conceito é o desse problema, evidência fraca.`
    : `Problemas ${listProblemIds(problemIds)}`
  return (
    <div className="concept-recurrence">
      <Tooltip text={title}>
        <button
          type="button"
          className="concept-recurrence__button"
          aria-expanded={isOpen}
          onClick={() => setIsOpen((current) => !current)}
        >
          {weak ? <TriangleAlert size={12} aria-label="evidência fraca" /> : null}
          {problemCount(problemIds.length)}
        </button>
      </Tooltip>
      {isOpen ? (
        <ul className="concept-recurrence__list">
          {problemIds.map((problemId) => (
            <li key={problemId}>Problema {problemId}</li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
