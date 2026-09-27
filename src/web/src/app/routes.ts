import type { ComponentType } from 'react'

import { ClassroomImportPage } from '../features/classroom_import/pages/ClassroomImportPage'
import { ClassroomPage } from '../features/classrooms/pages/ClassroomPage'
import { ClassroomsPage } from '../features/classrooms/pages/ClassroomsPage'
import { KnowledgeComponentsPage } from '../features/knowledge_components/pages/KnowledgeComponentsPage'
import { MasteryDashboardPage } from '../features/mastery_dashboard/pages/MasteryDashboardPage'
import { matchPath } from '../lib/hashRoute'

// O que o endereço carrega, a turma e, dentro dela, o exercício
export interface RouteParams {
  classroomId?: number
  assignmentId?: number
}

export interface Route {
  pattern: string
  Page: ComponentType<RouteParams>
}

// O contexto está no endereço, então F5 e links abrem no lugar certo sem nenhum seletor
export const ROUTES: Route[] = [
  { pattern: '/classrooms', Page: ClassroomsPage },
  { pattern: '/classrooms/:classroomId', Page: ClassroomPage },
  {
    pattern: '/classrooms/:classroomId/assignments/:assignmentId/knowledge-components',
    Page: KnowledgeComponentsPage,
  },
  {
    pattern: '/classrooms/:classroomId/assignments/:assignmentId/analysis',
    Page: MasteryDashboardPage,
  },
  { pattern: '/classroom-imports', Page: ClassroomImportPage },
]

export const HOME_PATH = '/classrooms'

export interface RouteMatch {
  route: Route
  params: RouteParams
}

// Sem hash, abre Turmas
export function matchRoute(path: string): RouteMatch | undefined {
  const target = path === '' ? HOME_PATH : path
  for (const route of ROUTES) {
    const params = matchPath(route.pattern, target)
    if (params) return { route, params }
  }
  return undefined
}
