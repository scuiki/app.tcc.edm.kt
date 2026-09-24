"""TrainedModel: uma versão treinada do Code-DKT (arquivos em disco + métricas no banco).

Write-once: uma versão gravada nunca muda; um novo treino é uma versão nova.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TrainedModel:
    id: int | None
    assignment_id: int
    version_number: int
    content_hash: str | None  # SHA-256 dos arquivos: integridade, não identidade
    model_dir: str  # onde os arquivos moram; o banco nunca guarda os bytes
    created_at: str
    first_attempt_auc: float | None = None
    # A proveniência: qual código (commit) e qual dado (hash do dado de treino) geraram a versão.
    git_commit: str | None = None
    data_hash: str | None = None
