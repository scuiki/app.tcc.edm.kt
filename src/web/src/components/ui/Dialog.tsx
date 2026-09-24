import { useEffect, useId, useRef, type ReactNode } from 'react'
import { CircleAlert } from 'lucide-react'

import './Dialog.css'

interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  // O de exclusão vira alertdialog, com o ícone de alerta ao lado do título
  tone?: 'default' | 'danger'
  children: ReactNode
}

// O dialog nativo já prende o foco, fecha no Esc e escurece o fundo
export function Dialog({ open, onClose, title, tone = 'default', children }: DialogProps) {
  const ref = useRef<HTMLDialogElement>(null)
  const titleId = useId()

  // Sincroniza a prop open com a API do DOM, o único jeito de abrir como modal
  useEffect(() => {
    const dialog = ref.current
    if (!dialog) return
    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  // O conteúdo só existe aberto, então um formulário nasce limpo a cada abertura
  return (
    <dialog
      ref={ref}
      className={`dialog dialog--${tone}`}
      role={tone === 'danger' ? 'alertdialog' : undefined}
      aria-labelledby={titleId}
      onClose={onClose}
    >
      {open ? (
        <>
          <div className="dialog__header">
            {tone === 'danger' ? (
              <CircleAlert className="dialog__alert-icon" size={20} aria-hidden="true" />
            ) : null}
            <h2 id={titleId} className="t-section-title">
              {title}
            </h2>
          </div>
          {children}
        </>
      ) : null}
    </dialog>
  )
}

export function DialogBody({ children }: { children: ReactNode }) {
  return <div className="dialog__body">{children}</div>
}

export function DialogFooter({ children }: { children: ReactNode }) {
  return <div className="dialog__footer">{children}</div>
}
