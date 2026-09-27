import type { ReactNode } from 'react'

import './ConceptChips.css'

interface Concept {
  kc_id: number
  kc_name: string
}

// Os conceitos de um problema, em etiquetas neutras; o `leading` entra na mesma fila, antes deles
export function ConceptChips({ concepts, leading }: { concepts: Concept[]; leading?: ReactNode }) {
  // Sem conceitos aprovados a lista vem vazia, e aí não há o que mostrar
  if (concepts.length === 0) return null
  return (
    <ul className="concept-chips" aria-label="Conceitos">
      {leading ? <li className="concept-chips__leading">{leading}</li> : null}
      {concepts.map((concept) => (
        <li key={concept.kc_id} className="concept-chip">
          {concept.kc_name}
        </li>
      ))}
    </ul>
  )
}
