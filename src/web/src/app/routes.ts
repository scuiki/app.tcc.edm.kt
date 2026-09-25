import type { ComponentType } from 'react'
import { Database, LayoutGrid, Layers, Users, type LucideIcon } from 'lucide-react'

import { ClassroomImportPage } from '../features/classroom_import/pages/ClassroomImportPage'
import { ClassroomsPage } from '../features/classrooms/pages/ClassroomsPage'
import { KnowledgeComponentsPage } from '../features/knowledge_components/pages/KnowledgeComponentsPage'
import { MasteryDashboardPage } from '../features/mastery_dashboard/pages/MasteryDashboardPage'

export interface Route {
  path: string
  label: string
  icon: LucideIcon
  Page: ComponentType
}

// A ordem é a do menu, e uma tela só entra aqui quando existe
export const ROUTES: Route[] = [
  { path: '/classrooms', label: 'Turmas', icon: Users, Page: ClassroomsPage },
  {
    path: '/classroom-imports',
    label: 'Importar dados',
    icon: Database,
    Page: ClassroomImportPage,
  },
  {
    path: '/knowledge-components',
    label: 'Conceitos',
    icon: Layers,
    Page: KnowledgeComponentsPage,
  },
  {
    path: '/mastery-dashboard',
    label: 'Domínio da turma',
    icon: LayoutGrid,
    Page: MasteryDashboardPage,
  },
]

// Sem hash, abre a primeira página do menu
export function findRoute(path: string): Route | undefined {
  if (path === '') return ROUTES[0]
  return ROUTES.find((route) => route.path === path)
}
