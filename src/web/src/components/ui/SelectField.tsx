import { useId, type ReactNode } from 'react'
import { ChevronDown } from 'lucide-react'

import './Field.css'

interface SelectOption {
  value: string
  label: string
}

interface SelectFieldProps {
  label: string
  value: string
  options: SelectOption[]
  onChange: (value: string) => void
  // O texto da opção vazia, que pede a escolha
  placeholder: string
  hint?: ReactNode
  required?: boolean
  disabled?: boolean
}

export function SelectField({
  label,
  value,
  options,
  onChange,
  placeholder,
  hint,
  required,
  disabled,
}: SelectFieldProps) {
  const id = useId()
  const hintId = `${id}-hint`
  return (
    <div className="field">
      <label htmlFor={id} className="field__label">
        {label}
        {required ? (
          <span className="field__required" aria-hidden="true">
            {' '}
            *
          </span>
        ) : null}
      </label>
      <div className="select-field">
        <select
          id={id}
          className="field__input select-field__input"
          value={value}
          required={required}
          disabled={disabled}
          aria-describedby={hint ? hintId : undefined}
          onChange={(event) => onChange(event.target.value)}
        >
          <option value="" disabled>
            {placeholder}
          </option>
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown className="select-field__chevron" size={16} aria-hidden="true" />
      </div>
      {hint ? (
        <span id={hintId} className="field__hint">
          {hint}
        </span>
      ) : null}
    </div>
  )
}
