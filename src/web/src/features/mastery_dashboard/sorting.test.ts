import { describe, expect, it } from 'vitest'

import { sortRows, toggleSort, type SortState } from './sorting'

type Key = 'rate' | 'median' | 'id'
const ROWS = [
  { id: '13', rate: 0.12, median: 5 },
  { id: '232', rate: 0.18, median: null },
  { id: '12', rate: 0.48, median: 1 },
  { id: '1', rate: 0.45, median: 1 },
]

describe('toggleSort', () => {
  it('starts ascending on a new column and flips on the same one', () => {
    const start: SortState<Key> = { key: 'rate', direction: 'asc' }
    expect(toggleSort(start, 'median')).toEqual({ key: 'median', direction: 'asc' })
    expect(toggleSort(start, 'rate')).toEqual({ key: 'rate', direction: 'desc' })
    expect(toggleSort(toggleSort(start, 'rate'), 'rate')).toEqual(start)
  })
})

describe('sortRows', () => {
  it('sorts numbers in both directions without touching the original list', () => {
    const asc = sortRows(ROWS, { key: 'rate', direction: 'asc' })
    const desc = sortRows(ROWS, { key: 'rate', direction: 'desc' })
    expect(asc.map((row) => row.id)).toEqual(['13', '232', '1', '12'])
    expect(desc.map((row) => row.id)).toEqual(['12', '1', '232', '13'])
    expect(ROWS[0].id).toBe('13')
  })

  it('keeps missing values last and ties in their original order', () => {
    const asc = sortRows(ROWS, { key: 'median', direction: 'asc' })
    const desc = sortRows(ROWS, { key: 'median', direction: 'desc' })
    expect(asc.map((row) => row.id)).toEqual(['12', '1', '13', '232'])
    expect(desc.map((row) => row.id)).toEqual(['13', '12', '1', '232'])
  })

  it('sorts identifiers as numbers when they look like numbers', () => {
    const asc = sortRows(ROWS, { key: 'id', direction: 'asc' })
    expect(asc.map((row) => row.id)).toEqual(['1', '12', '13', '232'])
  })
})
