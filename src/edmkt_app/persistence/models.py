"""Dataclasses das 8 entidades de domínio (D-01), espelhando o schema 0001.

Módulo de dados puro no estilo de config.py (__future__ annotations, type hints completos):
sem I/O, sem SQL — os repositórios (repositories.py) fazem o mapeamento linha↔objeto. Os
campos são SÓ os que esta fase exercita no round-trip (D-01); kc/qmatrix/mastery_prediction
nascem mínimas e crescem por ALTER TABLE nas fases 5-6.

Convenção de id: nasce None antes do insert; o repo devolve o lastrowid e o get() o repopula.
ModelArtifact é frozen (write-once por domínio, D-05/D-06), espelhando o MappingProxyType de
config.py:35.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional




@dataclass(frozen=True)
class ModelArtifact:
    id: Optional[int]
    assignment_id: int
    version_number: int
    content_hash: Optional[str]  # SHA-256 dos bytes: integridade/dedup, não identidade (D-04)
    artifact_dir: str  # caminho do blob no FS; NUNCA os bytes (CLAUDE.md §Persistência)
    created_at: str
    # first-attempt AUC do treino (DASH-05/D-05): nasce None nos artefatos pré-0007; train.py
    # grava no persist. É o valor que train.py já computa e hoje some com o subprocess.
    first_auc: Optional[float] = None
    git_commit: Optional[str] = None
    data_hash: Optional[str] = None


@dataclass
class MasteryPrediction:
    id: Optional[int]
    model_artifact_id: int
    subject_id: str
    kc_id: int
    mastery: Optional[float]


@dataclass
class TrainingJob:
    id: Optional[int]
    assignment_id: int
    status: str
    created_at: str
    # O progresso por época vive em training_metric; aqui só o total, gravado no mark_running.
    total_epochs: Optional[int] = None
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    error_message: Optional[str] = None
    # Taxa de parse javalang por-assignment (D-06 estendido/MODEL-05): nasce None; o subprocess
    # de treino grava no sucesso. Sobrevive ao término do processo filho (SC-3).
    parse_rate: Optional[float] = None
