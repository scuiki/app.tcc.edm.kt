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

export function useHashPath(): string {
  return pathOf(useSyncExternalStore(subscribe, readHash))
}
