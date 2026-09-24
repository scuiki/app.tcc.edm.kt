import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { CircleAlert, Inbox, LoaderCircle, type LucideIcon } from 'lucide-react'

import { Button } from '../ui/Button'
import './states.css'

const DEFAULT_ERROR = 'Não foi possível carregar os dados. Verifique se a API está no ar.'

// Nomeia o que está sendo feito, em vez de um giro sem legenda
export function LoadingState({ label }: { label: string }) {
  return (
    <div role="status" aria-live="polite" className="state">
      <LoaderCircle className="state__spinner" size={18} aria-hidden="true" />
      <p className="state__text">{label}</p>
    </div>
  )
}

interface ErrorStateProps {
  message?: string
  onRetry?: () => void
}

// Diz o que houve e qual é a saída, com o vermelho só no ícone
export function ErrorState({ message = DEFAULT_ERROR, onRetry }: ErrorStateProps) {
  return (
    <div role="alert" className="state">
      <CircleAlert className="state__error-icon" size={18} aria-hidden="true" />
      <p className="state__text">{message}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          Tentar de novo
        </Button>
      ) : null}
    </div>
  )
}

interface EmptyStateProps {
  icon?: LucideIcon
  title?: string
  text: string
  // A ação que leva ao próximo passo, e não só o aviso do que falta
  action?: ReactNode
}

export function EmptyState({ icon: Icon = Inbox, title, text, action }: EmptyStateProps) {
  return (
    <div role="status" className="state state--empty">
      <span className="state__icon-box">
        <Icon size={20} aria-hidden="true" />
      </span>
      {title ? <p className="state__title">{title}</p> : null}
      <p className="state__text">{text}</p>
      {action}
    </div>
  )
}

interface QueryStatesProps<T> {
  query: UseQueryResult<T>
  loadingLabel: string
  errorMessage?: string
  isEmpty?: (data: T) => boolean
  empty?: ReactNode
  children: (data: T) => ReactNode
}

// Os quatro estados de toda tela, na ordem carregando, erro, vazio e conteúdo
export function QueryStates<T>({
  query,
  loadingLabel,
  errorMessage,
  isEmpty,
  empty,
  children,
}: QueryStatesProps<T>) {
  if (query.isPending) return <LoadingState label={loadingLabel} />
  if (query.isError) return <ErrorState message={errorMessage} onRetry={() => query.refetch()} />
  if (empty && isEmpty?.(query.data)) return empty
  return children(query.data)
}
