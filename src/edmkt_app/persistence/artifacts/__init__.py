"""Persistência de artefatos de modelo: blob versionado no FS + ponteiro no banco.

`store` grava e recarrega o blob write-once; `versioning` cuida da numeração e do flip do
ponteiro. Os nomes seguem reexportados aqui — a divisão é de arquivo, não de contrato.
"""

from edmkt_app.persistence.artifacts.store import ArtifactStore
from edmkt_app.persistence.artifacts.versioning import flip_current, next_version_number

__all__ = ["ArtifactStore", "flip_current", "next_version_number"]
