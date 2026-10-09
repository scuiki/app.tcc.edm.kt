import { useEffect, useId, useRef, type ReactNode } from 'react'
import { CircleAlert } from 'lucide-react'

import './Dialog.css'

type DialogSize = 'default' | 'wide'

interface DialogProps {
  open: boolean
  onClose: () => void
  title: string
  // O de exclusão vira alertdialog, com o ícone de alerta ao lado do título
  tone?: 'default' | 'danger'
  // O largo, de 760px no lugar de 440px, cabe o código das soluções na origem do conceito
  size?: DialogSize
  // Logo depois do título e fora do h2, para o nome do diálogo continuar só o título
  titleAside?: ReactNode
  // A linha de fatos abaixo do título
  facts?: ReactNode
  // Falso enquanto algo roda e não pode ser largado no meio, e aí o Esc não fecha
  dismissible?: boolean
  children: ReactNode
}

// O dialog nativo já prende o foco, fecha no Esc e escurece o fundo
export function Dialog({
  open,
  onClose,
  title,
  tone = 'default',
  size = 'default',
  titleAside,
  facts,
  dismissible = true,
  children,
}: DialogProps) {
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
      className={size === 'wide' ? `dialog dialog--${tone} dialog--wide` : `dialog dialog--${tone}`}
      role={tone === 'danger' ? 'alertdialog' : undefined}
      aria-labelledby={titleId}
      onCancel={(event) => {
        if (!dismissible) event.preventDefault()
      }}
      onClose={() => {
        // O Chrome fecha no segundo Esc mesmo com o cancel bloqueado, então reabre
        if (!dismissible && open) ref.current?.showModal()
        else onClose()
      }}
    >
      {open ? (
        <>
          <div className="dialog__header">
            {tone === 'danger' ? (
              <CircleAlert className="dialog__alert-icon" size={20} aria-hidden="true" />
            ) : null}
            <div className="dialog__heading">
              <div className="dialog__title">
                <h2 id={titleId} className="t-section-title">
                  {title}
                </h2>
                {titleAside}
              </div>
              {facts}
            </div>
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
