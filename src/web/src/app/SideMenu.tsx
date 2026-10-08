import { useEffect, useRef, useState, type MouseEvent } from 'react'
import {
  Blocks,
  ChartColumn,
  ClipboardPen,
  Minus,
  Plus,
  Upload,
  Users,
  type LucideIcon,
} from 'lucide-react'

import {
  ASSIGNMENT_STATUS_LABEL,
  useAssignments,
  type AssignmentStatus,
  type AssignmentSummary,
} from '../features/assignments/api/useAssignments'
import { useClassrooms, type ClassroomSummary } from '../features/classrooms/api/classrooms'
import { Tooltip } from '../components/ui/Tooltip'
import { assignmentPath, classroomImportPath, classroomPath } from '../lib/paths'
import { HOME_PATH, type RouteParams } from './routes'
import './SideMenu.css'

interface SideMenuProps {
  path: string
  params: RouteParams
}

const STORAGE_KEY = 'edmkt.menu.expanded'

// O pronto para conceitos e o rascunho dividem o ponto vazio, e quem não treina fica sem ponto
type StatusDot = 'awaiting' | 'kc_approved' | 'trained'

const STATUS_DOT: Record<AssignmentStatus, StatusDot | undefined> = {
  statistics_only: undefined,
  ready_for_kc_generation: 'awaiting',
  kc_draft: 'awaiting',
  kc_approved: 'kc_approved',
  trained: 'trained',
}

const STATUS_DOT_LABEL: Record<StatusDot, string> = {
  awaiting: 'Aguardando conceitos',
  kc_approved: ASSIGNMENT_STATUS_LABEL.kc_approved,
  trained: ASSIGNMENT_STATUS_LABEL.trained,
}
const CLASSROOMS_KEY = 'classrooms'

// Os nós abertos ficam no navegador; o caminho da rota atual abre sempre
function readExpanded(): string[] {
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY)
    return stored ? (JSON.parse(stored) as string[]) : []
  } catch {
    return []
  }
}

function writeExpanded(keys: string[]) {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(keys))
  } catch {
    // Sem armazenamento, o menu só não lembra o que estava aberto
  }
}

const classroomKey = (classroomId: number) => `classroom:${classroomId}`
const assignmentKey = (assignmentId: number) => `assignment:${assignmentId}`

// O menu lista o que existe, turma › exercício › tela, recuado e com o mais e o menos na ponta
export function SideMenu({ path, params }: SideMenuProps) {
  // Só uma tela de exercício abre o caminho até ela, para a linha atual aparecer marcada
  const [expanded, setExpanded] = useState<string[]>(() => {
    const keys = new Set(readExpanded())
    if (params.classroomId != null && params.assignmentId != null) {
      keys.add(CLASSROOMS_KEY)
      keys.add(classroomKey(params.classroomId))
      keys.add(assignmentKey(params.assignmentId))
    }
    return [...keys]
  })
  const open = new Set(expanded)

  // O que a rota abriu fica gravado, senão a árvore se fechava ao sair para outra tela
  useEffect(() => {
    writeExpanded(expanded)
  }, [expanded])

  function toggle(key: string) {
    setExpanded(
      expanded.includes(key)
        ? expanded.filter((candidate) => candidate !== key)
        : [...expanded, key],
    )
  }

  return (
    <nav aria-label="Navegação principal" className="side-menu">
      <MenuRow
        href={HOME_PATH}
        label="Turmas"
        icon={Users}
        level="main"
        isCurrent={path === HOME_PATH}
        isOpen={open.has(CLASSROOMS_KEY)}
        onToggle={() => toggle(CLASSROOMS_KEY)}
      />
      {open.has(CLASSROOMS_KEY) ? (
        <ClassroomRows path={path} isOpen={(key) => open.has(key)} onToggle={toggle} />
      ) : null}
      <MenuRow
        href={classroomImportPath()}
        label="Importar dados"
        icon={Upload}
        level="main"
        isCurrent={path === classroomImportPath()}
      />
    </nav>
  )
}

interface ClassroomRowsProps {
  path: string
  isOpen: (key: string) => boolean
  onToggle: (key: string) => void
}

function ClassroomRows({ path, isOpen, onToggle }: ClassroomRowsProps) {
  const query = useClassrooms()
  if (query.isPending) return <p className="side-menu__note">Carregando…</p>
  const classrooms = query.data?.classrooms ?? []
  if (classrooms.length === 0) return <p className="side-menu__note">Nenhuma turma ainda</p>
  return (
    <>
      {classrooms.map((classroom) => (
        <ClassroomRow
          key={classroom.id}
          classroom={classroom}
          path={path}
          isOpen={isOpen}
          onToggle={onToggle}
        />
      ))}
    </>
  )
}

interface ClassroomRowProps {
  classroom: ClassroomSummary
  path: string
  isOpen: (key: string) => boolean
  onToggle: (key: string) => void
}

function ClassroomRow({ classroom, path, isOpen, onToggle }: ClassroomRowProps) {
  const key = classroomKey(classroom.id)
  const href = classroomPath(classroom.id)
  return (
    <>
      <MenuRow
        href={href}
        label={classroom.name}
        level="classroom"
        isCurrent={path === href}
        isOpen={isOpen(key)}
        onToggle={() => onToggle(key)}
      />
      {isOpen(key) ? (
        <AssignmentRows
          classroomId={classroom.id}
          path={path}
          isOpen={isOpen}
          onToggle={onToggle}
        />
      ) : null}
    </>
  )
}

interface AssignmentRowsProps {
  classroomId: number
  path: string
  isOpen: (key: string) => boolean
  onToggle: (key: string) => void
}

// Só a turma aberta busca os exercícios dela
function AssignmentRows({ classroomId, path, isOpen, onToggle }: AssignmentRowsProps) {
  const query = useAssignments(classroomId)
  if (query.isPending) return <p className="side-menu__note">Carregando…</p>
  const assignments = query.data?.assignments ?? []
  if (assignments.length === 0) return <p className="side-menu__note">Sem exercícios</p>
  return (
    <>
      {assignments.map((assignment) => (
        <AssignmentRow
          key={assignment.id}
          classroomId={classroomId}
          assignment={assignment}
          path={path}
          isOpen={isOpen(assignmentKey(assignment.id))}
          onToggle={() => onToggle(assignmentKey(assignment.id))}
        />
      ))}
    </>
  )
}

interface AssignmentRowProps {
  classroomId: number
  assignment: AssignmentSummary
  path: string
  isOpen: boolean
  onToggle: () => void
}

function AssignmentRow({ classroomId, assignment, path, isOpen, onToggle }: AssignmentRowProps) {
  const concepts = assignmentPath(classroomId, assignment.id, 'knowledge-components')
  const analysis = assignmentPath(classroomId, assignment.id, 'analysis')
  const dot = assignment.status ? STATUS_DOT[assignment.status] : undefined
  return (
    <>
      <MenuRow
        label={assignment.name}
        icon={ClipboardPen}
        level="assignment"
        isOpen={isOpen}
        onToggle={onToggle}
        status={dot ? STATUS_DOT_LABEL[dot] : undefined}
        statusKey={dot}
      />
      {isOpen ? (
        <>
          <MenuRow
            href={concepts}
            label="Conceitos"
            icon={Blocks}
            level="screen"
            isCurrent={path === concepts}
          />
          <MenuRow
            href={analysis}
            label="Análise"
            icon={ChartColumn}
            level="screen"
            isCurrent={path === analysis}
          />
        </>
      ) : null}
    </>
  )
}

interface MenuRowProps {
  label: string
  level: 'main' | 'classroom' | 'assignment' | 'screen'
  // Só a turma fica sem ícone, o nome dela já a distingue
  icon?: LucideIcon
  // Sem href a linha só abre e fecha, como o exercício
  href?: string
  isCurrent?: boolean
  isOpen?: boolean
  onToggle?: () => void
  status?: string
  statusKey?: string
}

// Uma linha do menu é um controle só, com o mais ou o menos dentro, e cada nível tem o seu recuo
function MenuRow({
  label,
  level,
  icon: Icon,
  href,
  isCurrent,
  isOpen,
  onToggle,
  status,
  statusKey,
}: MenuRowProps) {
  const signRef = useRef<HTMLSpanElement>(null)

  // Numa linha com link, escolher só navega; o sinal na ponta abre e fecha sem sair da tela
  function onLinkClick(event: MouseEvent<HTMLAnchorElement>) {
    if (onToggle && signRef.current?.contains(event.target as Node)) {
      event.preventDefault()
      onToggle()
    }
  }

  const content = (
    <>
      {Icon ? <Icon size={level === 'main' ? 17 : 15} aria-hidden="true" /> : null}
      <span className="side-menu__label">{label}</span>
      {status ? (
        <Tooltip text={status}>
          <span
            className={`side-menu__dot side-menu__dot--${statusKey}`}
            role="img"
            aria-label={status}
          />
        </Tooltip>
      ) : null}
      <span className="side-menu__spacer" />
      {onToggle ? (
        <span ref={signRef} className="side-menu__sign" aria-hidden="true">
          {isOpen ? <Minus size={14} /> : <Plus size={14} />}
        </span>
      ) : null}
    </>
  )
  const className = `side-menu__item side-menu__item--${level}`
  if (href) {
    return (
      <a
        href={`#${href}`}
        className={className}
        aria-current={isCurrent ? 'page' : undefined}
        aria-expanded={onToggle ? isOpen : undefined}
        onClick={onLinkClick}
      >
        {content}
      </a>
    )
  }
  return (
    <button type="button" className={className} aria-expanded={isOpen} onClick={onToggle}>
      {content}
    </button>
  )
}
