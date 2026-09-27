import { useSyncExternalStore } from 'react'

// A página atual mora no hash da URL, então F5 e o voltar do navegador funcionam sem roteador

function subscribe(onChange: () => void) {
  window.addEventListener('hashchange', onChange)
  return () => window.removeEventListener('hashchange', onChange)
}

function readHash() {
  return window.location.hash
}

// O caminho sem o # e sem a query, com '#/classrooms?x=1' virando '/classrooms'
export function pathOf(hash: string): string {
  return hash.replace(/^#/, '').split('?')[0]
}

// Um parâmetro da query do hash, com '#/classroom-imports?classroom=3' dando '3' para classroom
export function hashParam(hash: string, name: string): string | null {
  const query = hash.split('?')[1] ?? ''
  return new URLSearchParams(query).get(name)
}

export type PathParams = Record<string, number>

// Casa `/classrooms/:classroomId` com `/classrooms/3` e devolve `{ classroomId: 3 }`
export function matchPath(pattern: string, path: string): PathParams | null {
  const expected = pattern.split('/')
  const actual = path.split('/')
  if (expected.length !== actual.length) return null
  const params: PathParams = {}
  for (let index = 0; index < expected.length; index += 1) {
    const segment = expected[index]
    if (!segment.startsWith(':')) {
      if (segment !== actual[index]) return null
      continue
    }
    const value = Number(actual[index])
    if (actual[index] === '' || !Number.isInteger(value) || value <= 0) return null
    params[segment.slice(1)] = value
  }
  return params
}

export function useHashPath(): string {
  return pathOf(useSyncExternalStore(subscribe, readHash))
}
