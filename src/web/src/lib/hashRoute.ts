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

// Um parâmetro da query do hash, com '#/knowledge-components?classroom=3' dando '3' para classroom
export function hashParam(hash: string, name: string): string | null {
  const query = hash.split('?')[1] ?? ''
  return new URLSearchParams(query).get(name)
}

export function useHashPath(): string {
  return pathOf(useSyncExternalStore(subscribe, readHash))
}
