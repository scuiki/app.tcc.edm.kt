import type { ReactNode } from 'react'

import './PageActionBar.css'

// A barra fixa no pé da página, com o que o próximo clique faz e os botões
export function PageActionBar({ message, children }: { message: string; children: ReactNode }) {
  return (
    <div className="page-action-bar">
      <span className="page-action-bar__message">{message}</span>
      {children}
    </div>
  )
}
