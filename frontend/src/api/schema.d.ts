// Hand-written API contract for the Phase 6 dashboard endpoints.
//
// The canonical generator is `npx openapi-typescript http://127.0.0.1:8099/openapi.json`, but the
// FastAPI app only runs inside the Docker image (container-only isolation: the nitro host is kept
// clean, no host venv/pip — STATE.md). With no importable uvicorn here, these types are transcribed
// by hand DIRECTLY from the backend DTOs (e.g. src/api/mastery_dashboard/application/dtos/
// mastery_dashboard_dto.py) — the source of truth, not the UI-SPEC abbreviations. Regenerate
// from /openapi.json once the api service is up to remove drift.
//
// Pitfall 1 (RESEARCH): `students_at_risk` is `string[]` (student_ids), NOT object[]. The backend
// returns find_students_at_risk(matrix) -> list[str] (mastery_level.py).

// GET /assignments -> api/assignments/application/dtos/list_assignments_dto.py
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
  student_id: string;
  kc_id: number;
  mastery: number;
}

// One weakest-first critical KC entry (DASH-02); ordering is authored by the backend, never re-sorted.
export interface CriticalKC {
  kc_id: number;
  mean_mastery: number;
}

// GET /mastery-dashboard/{assignment_id}/mastery -> MasteryResponseDTO
export interface MasteryResponse {
  assignment_id: number;
  /** DASH-05/D-08 uncertainty frame — null when no model is published (untrained) */
  first_attempt_auc: number | null;
  /** model_artifact.created_at; null when untrained */
  trained_at: string | null;
  matrix: MasteryCell[];
  critical_kcs: CriticalKC[];
  /** Pitfall 1: student_ids as plain strings, not objects (DASH-03) */
  students_at_risk: string[];
}

// Pre-training statistics: the backend serializes dict[int, float]; int keys become JSON string keys.
// Each is `{}` when the canonical Parquet is absent (DASH-04, no model needed).
export type EdaAggregate = Record<string, number>;

// GET /mastery-dashboard/{assignment_id}/pre-training-statistics -> PreTrainingStatisticsResponseDTO
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

// GET /mastery-dashboard/{assignment_id}/recommendations -> RecommendationsResponseDTO
export interface RecommendationsResponse {
  assignment_id: number;
  recommendations: Recommendation[];
}
