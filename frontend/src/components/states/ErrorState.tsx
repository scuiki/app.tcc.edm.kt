// Error state (API unreachable / non-ok). Copy is locked verbatim in the UI-SPEC Copywriting
// Contract. Rendered as plain JSX text (React auto-escapes); no raw-HTML injection (V5).

export function ErrorState() {
  return (
    <div role="alert">
      Não foi possível carregar os dados do dashboard. Verifique se a API está no ar e tente
      novamente.
    </div>
  )
}
