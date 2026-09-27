import type { LucideIcon } from 'lucide-react'

import './Tabs.css'

export interface TabItem<K extends string> {
  key: K
  label: string
  icon?: LucideIcon
}

interface TabsProps<K extends string> {
  items: TabItem<K>[]
  active: K
  onChange: (key: K) => void
  label: string
}

// Abas no topo de um cartão; a ativa leva o azul e o fio embaixo, como a página atual no menu
export function Tabs<K extends string>({ items, active, onChange, label }: TabsProps<K>) {
  return (
    <div role="tablist" aria-label={label} className="tabs">
      {items.map(({ key, label: text, icon: Icon }) => (
        <button
          key={key}
          type="button"
          role="tab"
          aria-selected={key === active}
          className="tabs__tab"
          onClick={() => onChange(key)}
        >
          {Icon ? <Icon size={15} aria-hidden="true" /> : null}
          <span>{text}</span>
        </button>
      ))}
    </div>
  )
}
