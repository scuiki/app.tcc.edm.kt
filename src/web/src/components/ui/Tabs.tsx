import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import './Tabs.css'

export interface TabItem<K extends string> {
  key: K
  label: string
  icon?: LucideIcon
  // O nome para o leitor de tela quando o texto da aba não diz tudo, como só o número do problema
  ariaLabel?: string
}

interface TabsProps<K extends string> {
  items: TabItem<K>[]
  active: K
  onChange: (key: K) => void
  label: string
  // O rótulo à esquerda das abas, escondido do leitor de tela porque cada aba já tem o nome inteiro
  leading?: ReactNode
  // As ações do cartão à direita, fora da tablist
  actions?: ReactNode
}

// Abas no topo de um cartão; a ativa leva o texto escuro, o negrito e o fio embaixo
export function Tabs<K extends string>({
  items,
  active,
  onChange,
  label,
  leading,
  actions,
}: TabsProps<K>) {
  return (
    <div className="tabs">
      {leading ? (
        <span className="tabs__label" aria-hidden="true">
          {leading}
        </span>
      ) : null}
      <div role="tablist" aria-label={label} className="tabs__list">
        {items.map(({ key, label: text, icon: Icon, ariaLabel }) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={key === active}
            aria-label={ariaLabel}
            className="tabs__tab"
            onClick={() => onChange(key)}
          >
            {Icon ? <Icon size={15} aria-hidden="true" /> : null}
            <span>{text}</span>
          </button>
        ))}
      </div>
      {actions ? <div className="tabs__actions">{actions}</div> : null}
    </div>
  )
}
