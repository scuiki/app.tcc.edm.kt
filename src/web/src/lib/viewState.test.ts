import { describe, expect, it } from 'vitest'

import { masteryViewState, edaViewState } from './viewState'
import {
  edaNoData,
  edaWithData,
  masteryTrained,
  masteryUntrained,
} from '../test/fixtures'

// The two non-verdict states are distinct (Pitfall 4): "model not trained" (mastery) vs "no data yet"
// (eda). They drive different downstream copy, so the discriminators must never conflate them — and an
// empty matrix must never collapse into "zero mastery" (Pitfall 2, the all-red trap).

describe('masteryViewState', () => {
  it('reports untrained when first_attempt_auc is null and the matrix is empty', () => {
    expect(masteryViewState(masteryUntrained)).toBe('untrained')
  })

  it('reports ready when a model is published with a non-empty matrix', () => {
    expect(masteryViewState(masteryTrained)).toBe('ready')
  })
})

describe('edaViewState', () => {
  it('reports empty when all three aggregates are empty', () => {
    expect(edaViewState(edaNoData)).toBe('empty')
  })

  it('reports ready when at least one aggregate has keys', () => {
    expect(edaViewState(edaWithData)).toBe('ready')
  })
})

describe('the two non-verdict states are never conflated', () => {
  it('untrained mastery is not reported as eda-empty, nor vice versa', () => {
    // Each discriminator owns its own vocabulary: mastery yields untrained/ready, eda yields
    // empty/ready. "untrained" and "empty" are different tokens by construction.
    expect(masteryViewState(masteryUntrained)).not.toBe(edaViewState(edaNoData))
  })
})
