import { useId } from 'react'
import { Search } from 'lucide-react'

import './Field.css'

interface SearchFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
}

// A busca compacta de 32px, com o rótulo só para o leitor de tela
export function SearchField({ label, value, onChange }: SearchFieldProps) {
  const id = useId()
  return (
    <div className="search-field">
      <Search className="search-field__icon" size={15} aria-hidden="true" />
      <label htmlFor={id} className="visually-hidden">
        {label}
      </label>
      <input
        id={id}
        type="search"
        className="search-field__input"
        placeholder={label}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  )
}
