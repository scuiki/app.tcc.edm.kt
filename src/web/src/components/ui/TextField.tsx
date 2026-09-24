import { useId, type InputHTMLAttributes } from 'react'

import './Field.css'

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type' | 'id'> {
  label: string
  hint?: string
  // A recusa aparece no lugar da ajuda, em vermelho, com o contorno do campo também em vermelho
  error?: string
}

export function TextField({ label, hint, error, required, ...rest }: TextFieldProps) {
  const id = useId()
  const messageId = `${id}-message`
  const message = error ?? hint
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
      <input
        id={id}
        type="text"
        className="field__input"
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={message ? messageId : undefined}
        {...rest}
      />
      {message ? (
        <span id={messageId} className={error ? 'field__error' : 'field__hint'}>
          {message}
        </span>
      ) : null}
    </div>
  )
}
