// Non-verdict state discriminators for the two read-only views. They separate "model not trained yet"
// (mastery) from "no data ingested yet" (eda) — two distinct empty states that route to different copy
// downstream (Pitfall 4). The error/loading states are the query layer's job, not these helpers'.

import type { EdaResponse, MasteryResponse } from '../api/schema'

export type MasteryViewState = 'ready' | 'untrained'
export type EdaViewState = 'ready' | 'empty'

// Untrained == the uncertainty frame is null AND the matrix is empty (dashboard.py returns both
// together when no model is published). An empty matrix is NOT zero mastery — never render it as such
// (Pitfall 2, the all-red trap).
export function masteryViewState(resp: MasteryResponse): MasteryViewState {
  if (resp.first_auc == null && resp.matrix.length === 0) return 'untrained'
  return 'ready'
}

// Empty == all three EDA aggregates are keyless (the canonical Parquet is absent, dashboard.py degrades
// to {} rather than 500). One populated aggregate is enough to render.
export function edaViewState(resp: EdaResponse): EdaViewState {
  const empty =
    Object.keys(resp.success_rate).length === 0 &&
    Object.keys(resp.learning_curve).length === 0 &&
    Object.keys(resp.compile_error_rate).length === 0
  return empty ? 'empty' : 'ready'
}
