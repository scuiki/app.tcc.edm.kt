// Error state (API unreachable / non-ok). Copy is locked verbatim in the UI-SPEC Copywriting
// Contract. Rendered as plain JSX text (React auto-escapes); no raw-HTML injection (V5).

import { AlertTriangle } from 'lucide-react'

export function ErrorState() {
  return (
    <div role="alert" className="state state--error">
      <AlertTriangle className="state__icon" size={18} aria-hidden="true" />
      <p className="state__text">
        Não foi possível carregar os dados do dashboard. Verifique se a API está no ar e tente
        novamente.
      </p>
    </div>
  )
}
