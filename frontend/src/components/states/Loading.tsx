// Loading state. Copy is locked verbatim in the UI-SPEC Copywriting Contract.

import { Loader2 } from 'lucide-react'

export function Loading() {
  return (
    <div role="status" aria-live="polite" className="state">
      <Loader2 className="state__icon" size={18} aria-hidden="true" />
      <p className="state__text">Carregando dados da turma…</p>
    </div>
  )
}
