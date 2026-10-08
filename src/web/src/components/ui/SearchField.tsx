import { Search } from 'lucide-react'

import './Field.css'

interface SearchFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
}

// A busca compacta de 32px, e a caixa inteira é o rótulo, para o clique na lupa focar o campo
export function SearchField({ label, value, onChange }: SearchFieldProps) {
  return (
    <label className="search-field">
      <Search className="search-field__icon" size={15} aria-hidden="true" />
      <span className="visually-hidden">{label}</span>
      <input
        type="search"
        className="search-field__input"
        placeholder={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  )
}
