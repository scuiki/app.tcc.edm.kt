// Os números e as datas que o backend manda, formatados em pt-BR sem nenhum recálculo

const PLACEHOLDER = '—'

const dateFormat = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short' })
const dateTimeFormat = new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
const countFormat = new Intl.NumberFormat('pt-BR')

// Percentual inteiro, com o mesmo arredondamento do {.0%} do backend
export function formatPercent(value: number | null | undefined): string {
  if (value == null) return PLACEHOLDER
  return `${Math.round(value * 100)}%`
}

export function formatCount(value: number): string {
  return countFormat.format(value)
}

// A data no fuso de quem está vendo, porque o backend grava em UTC
export function formatDate(iso: string): string {
  return dateFormat.format(new Date(iso))
}

export function formatDateTime(iso: string): string {
  return dateTimeFormat.format(new Date(iso)).replace(',', '')
}
