// A ordenação das tabelas vive no front, sobre a lista que a api devolveu de uma vez

export type SortDirection = 'asc' | 'desc'

export interface SortState<K extends string> {
  key: K
  direction: SortDirection
}

// Clicar na coluna já ativa inverte a direção, clicar em outra começa crescente
export function toggleSort<K extends string>(state: SortState<K>, key: K): SortState<K> {
  if (state.key !== key) return { key, direction: 'asc' }
  return { key, direction: state.direction === 'asc' ? 'desc' : 'asc' }
}

type SortableValue = number | string | null | undefined

// Devolve uma cópia ordenada, os valores ausentes sempre por último e o empate na ordem original
export function sortRows<K extends string, T extends Record<K, SortableValue>>(
  rows: T[],
  state: SortState<K>,
): T[] {
  const sign = state.direction === 'asc' ? 1 : -1
  return rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => {
      const first = a.row[state.key]
      const second = b.row[state.key]
      // O ausente vai para o fim nas duas direções, por isso fica fora do sinal
      if (first == null || second == null) {
        if (first == null && second == null) return a.index - b.index
        return first == null ? 1 : -1
      }
      const byValue = compare(first, second)
      return byValue === 0 ? a.index - b.index : byValue * sign
    })
    .map(({ row }) => row)
}

function compare(a: number | string, b: number | string): number {
  if (typeof a === 'number' && typeof b === 'number') return a - b
  return String(a).localeCompare(String(b), 'pt-BR', { numeric: true })
}
