import { GraduationCap } from 'lucide-react'

import { EmptyState } from '../components/states/states'
import { Card } from '../components/ui/Card'
import { useHashPath } from '../lib/hashRoute'
import { ErrorBoundary } from './ErrorBoundary'
import { findRoute, ROUTES, type Route } from './routes'
import './App.css'

export function App() {
  const path = useHashPath()
  const route = findRoute(path)
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
        <SideMenu routes={ROUTES} activePath={route?.path} />
        <main className="app__main">
          <ErrorBoundary key={path}>{route ? <route.Page /> : <PageNotFound />}</ErrorBoundary>
        </main>
      </div>
    </div>
  )
}

function SideMenu({ routes, activePath }: { routes: Route[]; activePath?: string }) {
  return (
    <nav aria-label="Navegação principal" className="side-menu">
      {routes.map(({ path, label, icon: Icon }) => (
        <a
          key={path}
          href={`#${path}`}
          className="side-menu__item"
          aria-current={path === activePath ? 'page' : undefined}
        >
          <Icon size={17} aria-hidden="true" />
          <span>{label}</span>
        </a>
      ))}
    </nav>
  )
}

function PageNotFound() {
  return (
    <Card title="Página não encontrada">
      <EmptyState
        text="O endereço não corresponde a nenhuma tela."
        action={<a href={`#${ROUTES[0].path}`}>Ir para {ROUTES[0].label}</a>}
      />
    </Card>
  )
}
