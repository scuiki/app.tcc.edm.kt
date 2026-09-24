// Hand-written API contract for the Phase 6 dashboard endpoints.
//
// The canonical generator is `npx openapi-typescript http://127.0.0.1:8099/openapi.json`, but the
// FastAPI app only runs inside the Docker image (container-only isolation: the nitro host is kept
// clean, no host venv/pip — STATE.md). With no importable uvicorn here, these types are transcribed
// by hand DIRECTLY from src/edmkt_app/api/dashboard.py — the source of truth, not the UI-SPEC
// abbreviations. Regenerate from /openapi.json once the api service is up to remove drift.
//
// Pitfall 1 (RESEARCH): `at_risk_students` is `string[]` (subject_ids), NOT object[]. dashboard.py
// returns edmkt_core.mastery.at_risk_students(matrix) -> list[str].

// GET /assignments -> api/assignments/application/list_assignments_dto.py
export interface AssignmentSummary {
  /** internal DB id (autoincrement) */
  id: number;
  /** the dataset's AssignmentID (e.g. 439); null when the assignment did not come from an import */
  progsnap_assignment_id: number | null;
  name: string;
  status: string | null;
  /** null until a trained model is published (untrained assignment) */
  published_model_id: number | null;
}

export interface AssignmentsResponse {
  assignments: AssignmentSummary[];
}

// One student x KC cell of the flattened mastery matrix (DASH-01).
export interface MasteryCell {
  subject_id: string;
  kc_id: number;
  mastery: number;
}

// One weakest-first critical KC entry (DASH-02); ordering is authored by the backend, never re-sorted.
export interface CriticalKC {
  kc_id: number;
  mean_mastery: number;
}

// GET /dashboard/mastery/{assignment_id} -> dashboard.py::get_mastery
export interface MasteryResponse {
  assignment_id: number;
  /** DASH-05/D-08 uncertainty frame — null when no model is published (untrained) */
  first_auc: number | null;
  /** model_artifact.created_at; null when untrained */
  trained_at: string | null;
  matrix: MasteryCell[];
  critical_kcs: CriticalKC[];
  /** Pitfall 1: subject_ids as plain strings, not objects (DASH-03) */
  at_risk_students: string[];
}

// EDA aggregates: dashboard.py serializes dict[int, float]; int keys become JSON string keys.
// Each is `{}` when the canonical Parquet is absent (DASH-04, no model needed).
export type EdaAggregate = Record<string, number>;

// GET /dashboard/eda/{assignment_id} -> dashboard.py::get_eda
export interface EdaResponse {
  assignment_id: number;
  success_rate: EdaAggregate;
  learning_curve: EdaAggregate;
  compile_error_rate: EdaAggregate;
}

// One reinforcement suggestion (REC-01); `text` is pre-rendered pt-BR, displayed verbatim.
export interface Recommendation {
  kc_id: number;
  kc_name: string;
  mean_mastery: number;
  text: string;
}

// GET /dashboard/recommendations/{assignment_id} -> dashboard.py::get_recommendations
export interface RecommendationsResponse {
  assignment_id: number;
  recommendations: Recommendation[];
}
