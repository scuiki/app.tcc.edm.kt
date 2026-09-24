# TrainedModel, uma versão treinada do Code-DKT (arquivos em disco + métricas no banco), write-once.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainedModel:
    id: int | None
    assignment_id: int
    version_number: int
    content_hash: str | None  # SHA-256 dos arquivos, prova de integridade, não identidade
    model_dir: str  # onde os arquivos moram; o banco nunca guarda os bytes
    created_at: str
    first_attempt_auc: float | None = None
    # A proveniência, qual código (commit) e qual dado (hash do dado) geraram a versão.
    git_commit: str | None = None
    data_hash: str | None = None
