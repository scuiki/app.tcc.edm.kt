import type { ButtonHTMLAttributes } from 'react'
import type { LucideIcon } from 'lucide-react'

import { Tooltip } from './Tooltip'
import './Button.css'

// Cada variante tem a sua situação de uso, e nenhum botão recebe cor por fora
type ButtonVariant = 'primary' | 'secondary' | 'destructive'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant: ButtonVariant
  icon?: LucideIcon
  // O compacto encosta nas etiquetas de 28px, como o Adicionar de cada problema
  size?: 'default' | 'compact'
}

export function Button({
  variant,
  icon: Icon,
  size = 'default',
  type = 'button',
  children,
  ...rest
}: ButtonProps) {
  return (
    <button type={type} className={`btn btn--${variant} btn--${size}`} {...rest}>
      {Icon ? <Icon size={15} strokeWidth={2.4} aria-hidden="true" /> : null}
      {children}
    </button>
  )
}

interface IconButtonProps extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'> {
  icon: LucideIcon
  // O nome da ação e do registro, porque o leitor de tela não enxerga o ícone
  label: string
}

export function IconButton({ icon: Icon, label, type = 'button', ...rest }: IconButtonProps) {
  return (
    <Tooltip text={label}>
      <button type={type} className="icon-btn" aria-label={label} {...rest}>
        <Icon size={16} aria-hidden="true" />
      </button>
    </Tooltip>
  )
}
