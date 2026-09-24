import type { ReactNode } from 'react'

import './ImportActionBar.css'

// A barra fixa no pé da página, com o que o próximo clique faz e os botões
export function ImportActionBar({ message, children }: { message: string; children: ReactNode }) {
  return (
    <div className="import-action-bar">
      <span className="import-action-bar__message">{message}</span>
      {children}
    </div>
  )
}
