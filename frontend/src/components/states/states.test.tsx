import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { Loading } from './Loading'
import { ErrorState } from './ErrorState'
import { EmptyState } from './EmptyState'

// Each state must render its EXACT locked copy from the UI-SPEC Copywriting Contract — these strings
// are the contract, so the assertions are verbatim (including the ellipsis character).

describe('Loading', () => {
  it('renders the locked loading copy', () => {
    render(<Loading />)
    expect(screen.getByText('Carregando dados da turma…')).toBeInTheDocument()
  })
})

describe('ErrorState', () => {
  it('renders the locked error copy', () => {
    render(<ErrorState />)
    expect(
      screen.getByText(
        'Não foi possível carregar os dados do dashboard. Verifique se a API está no ar e tente novamente.',
      ),
    ).toBeInTheDocument()
  })
})

describe('EmptyState', () => {
  it('renders the no-assignments heading and body', () => {
    render(<EmptyState kind="no-assignments" />)
    expect(screen.getByText('Nenhum assignment disponível')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Suba e processe um dataset ProgSnap2 para que os assignments apareçam aqui.',
      ),
    ).toBeInTheDocument()
  })

  it('renders the EDA no-data heading and body', () => {
    render(<EmptyState kind="eda" />)
    expect(screen.getByText('Sem dados para análise ainda')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Conclua a ingestão de um dataset desta turma para ver taxa de acerto, curvas de aprendizado e erros de compilação.',
      ),
    ).toBeInTheDocument()
  })

  it('renders the mastery-untrained copy', () => {
    render(<EmptyState kind="mastery-untrained" />)
    expect(
      screen.getByText(
        'Sem heatmap de domínio até o treino do Code-DKT concluir. Veja a EDA enquanto isso.',
      ),
    ).toBeInTheDocument()
  })

  it('renders the recs-untrained copy', () => {
    render(<EmptyState kind="recs-untrained" />)
    expect(
      screen.getByText(
        'As recomendações de reforço aparecem após o treino, a partir dos KCs de menor domínio.',
      ),
    ).toBeInTheDocument()
  })

  it('renders the select-assignment heading and body', () => {
    render(<EmptyState kind="select-assignment" />)
    expect(screen.getByText('Selecione um assignment')).toBeInTheDocument()
    expect(
      screen.getByText(
        'Escolha uma turma na lista à esquerda para ver domínio, análise exploratória e recomendações.',
      ),
    ).toBeInTheDocument()
  })
})
