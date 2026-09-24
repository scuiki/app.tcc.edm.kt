import { Component, type ReactNode } from 'react'

import { ErrorState } from '../components/states/states'

interface ErrorBoundaryState {
  hasError: boolean
}

// Uma exceção de render vira uma mensagem com saída, e não a tela em branco
export class ErrorBoundary extends Component<{ children: ReactNode }, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  // O React só oferece o boundary em classe, não existe hook para isso
  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorState
          message="Algo deu errado nesta tela. Recarregue a página para tentar de novo."
          onRetry={() => window.location.reload()}
        />
      )
    }
    return this.props.children
  }
}
