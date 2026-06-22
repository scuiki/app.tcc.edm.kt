// Per-state API response fixtures, mirroring the backend's fixture-per-state discipline in
// tests/test_api_dashboard.py. Shapes match src/edmkt_app/api/dashboard.py exactly (typed against
// schema.d.ts), so a contract drift breaks the type-check here, not at runtime.
//
// The four states (RESEARCH Validation Architecture): trained / untrained / no-data / error. The
// error state is exercised by the fetchJson throw path (Error("API <status>")), not a JSON body.

import type {
  AssignmentsResponse,
  EdaResponse,
  MasteryResponse,
  RecommendationsResponse,
} from '../api/schema'

// Trained: non-empty matrix, populated uncertainty frame, weakest-first critical KCs,
// at_risk_students as a plain string[] (Pitfall 1 — subject_ids, never objects).
export const masteryTrained: MasteryResponse = {
  assignment_id: 1,
  first_auc: 0.76,
  trained_at: '2026-06-21T00:00:00Z',
  matrix: [
    { subject_id: 's1', kc_id: 439, mastery: 0.31 },
    { subject_id: 's1', kc_id: 440, mastery: 0.82 },
    { subject_id: 's2', kc_id: 439, mastery: 0.55 },
    { subject_id: 's2', kc_id: 440, mastery: 0.68 },
  ],
  critical_kcs: [
    { kc_id: 439, mean_mastery: 0.43 },
    { kc_id: 440, mean_mastery: 0.75 },
  ],
  at_risk_students: ['s1', 's2'],
}

// Untrained: no published model — null uncertainty frame, empty matrix, no at-risk students.
export const masteryUntrained: MasteryResponse = {
  assignment_id: 2,
  first_auc: null,
  trained_at: null,
  matrix: [],
  critical_kcs: [],
  at_risk_students: [],
}

// EDA with data: int keys serialize as JSON string keys (Record<string, number>).
export const edaWithData: EdaResponse = {
  assignment_id: 1,
  success_rate: { '439': 0.5, '440': 0.72 },
  learning_curve: { '0': 0.2, '1': 0.45, '2': 0.6 },
  compile_error_rate: { '439': 0.18, '440': 0.09 },
}

// EDA no data: every aggregate is {} (no canonical Parquet yet).
export const edaNoData: EdaResponse = {
  assignment_id: 2,
  success_rate: {},
  learning_curve: {},
  compile_error_rate: {},
}

// Recommendations: pre-rendered pt-BR `text` shown verbatim (REC-01).
export const recommendations: RecommendationsResponse = {
  assignment_id: 1,
  recommendations: [
    {
      kc_id: 439,
      kc_name: 'Laços de repetição',
      mean_mastery: 0.43,
      text: 'Laços de repetição: domínio parcial — vale revisar (mastery média 43%).',
    },
    {
      kc_id: 440,
      kc_name: 'Condicionais',
      mean_mastery: 0.75,
      text: 'Condicionais: domínio consolidado (mastery média 75%).',
    },
  ],
}

// Assignments list: one trained (current_version_id set), one untrained (null).
export const assignments: AssignmentsResponse = {
  assignments: [
    {
      id: 1,
      progsnap_id: 439,
      name: 'Assignment 439',
      status: 'trained',
      current_version_id: 7,
    },
    {
      id: 2,
      progsnap_id: 440,
      name: 'Assignment 440',
      status: 'kc_approved',
      current_version_id: null,
    },
  ],
}
