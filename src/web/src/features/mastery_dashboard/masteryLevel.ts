// Os mesmos cortes de classify_mastery_level no backend, e o teste quebra se eles divergirem

export const LOW_LEVEL_CUTOFF = 0.4
export const HIGH_LEVEL_CUTOFF = 0.7

export type MasteryLevel = 'low' | 'medium' | 'high'

// O 0,70 ainda é médio, porque o corte de cima é inclusivo
export function classifyMasteryLevel(mastery: number): MasteryLevel {
  if (mastery < LOW_LEVEL_CUTOFF) return 'low'
  if (mastery <= HIGH_LEVEL_CUTOFF) return 'medium'
  return 'high'
}
