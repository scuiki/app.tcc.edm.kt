"""Repositórios por entidade: round-trip linha↔dataclass à mão sobre sqlite3 puro (D-03/SC4).

Um arquivo por entidade. Cada repo recebe a conexão e expõe `insert(obj) -> int` (via
`cursor.lastrowid`, não a cláusula pós-3.35 — Pitfall 7, o SQLite do container pode ser
pré-3.35) e `get(id) -> dataclass | None`.

TODO SQL é parametrizado com placeholders `?` (V5/T-02-04); nenhum dado é interpolado em string.

Os nomes são reexportados aqui para que `SqliteClassroomRepository` siga funcionando nos call sites
— a divisão é de arquivo, não de contrato.
"""

from edmkt_app.persistence.repositories.kc import KCRepository
from edmkt_app.persistence.repositories.kc_job import KCJobRepository
from edmkt_app.persistence.repositories.mastery_prediction import MasteryPredictionRepository
from edmkt_app.persistence.repositories.model_artifact import ModelArtifactRepository
from edmkt_app.persistence.repositories.qmatrix import QMatrixRepository
from edmkt_app.persistence.repositories.submission import SubmissionRepository
from edmkt_app.persistence.repositories.training_job import TrainingJobRepository
from edmkt_app.persistence.repositories.training_metric import TrainingMetricRepository

__all__ = [
    "KCJobRepository",
    "KCRepository",
    "MasteryPredictionRepository",
    "ModelArtifactRepository",
    "QMatrixRepository",
    "SubmissionRepository",
    "TrainingJobRepository",
    "TrainingMetricRepository",
]
