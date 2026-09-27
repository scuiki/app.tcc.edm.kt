import { GraduationCap } from 'lucide-react'

import { EmptyState } from '../components/states/states'
import { Card } from '../components/ui/Card'
import { useHashPath } from '../lib/hashRoute'
import { ErrorBoundary } from './ErrorBoundary'
import { HOME_PATH, matchRoute } from './routes'
import { SideMenu } from './SideMenu'
import './App.css'

export function App() {
  const path = useHashPath()
  const match = matchRoute(path)
  // A key zera o boundary ao trocar de página, e a tela nova começa sem o erro da anterior
  return (
    <div className="app">
      <header className="topbar">
        <GraduationCap
          className="topbar__icon"
          size={26}
          role="img"
          aria-label="EDM·KT, ferramenta docente"
        />
      </header>
      <div className="app__body">
        <SideMenu key={path} path={path === '' ? HOME_PATH : path} params={match?.params ?? {}} />
        <main className="app__main">
          <ErrorBoundary key={path}>
            {match ? <match.route.Page {...match.params} /> : <PageNotFound />}
          </ErrorBoundary>
        </main>
      </div>
    </div>
  )
}

function PageNotFound() {
  return (
    <Card title="Página não encontrada">
      <EmptyState
        text="O endereço não corresponde a nenhuma tela."
        action={<a href={`#${HOME_PATH}`}>Ir para Turmas</a>}
      />
    </Card>
  )
}
