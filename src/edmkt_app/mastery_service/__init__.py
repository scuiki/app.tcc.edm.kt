"""Orquestração impura do mastery (D-04): load → infer → aggregate → persist.

Camada DIP que liga o modelo Code-DKT treinado + a Q-matrix aprovada ao seam PURO
`ml.mastery`. Toma o quadro de modelagem pronto de `modeling_frame` (nunca o Parquet
cru — training-serving skew), recarrega o artefato, infere e mapeia ProblemID→KC pela Q-matrix.
TODO I/O de FS/SQLite/torch vive aqui; toda agregação fica no core puro.

Divisão: `inference` (artefato → pred_df) · `materialization`
(pred_df → matriz persistida, compute-once).

Os nomes seguem reexportados — a divisão é de arquivo, não de contrato.
"""

from edmkt_app.mastery_service.inference import infer_predictions
from edmkt_app.mastery_service.materialization import compute_mastery

__all__ = ["compute_mastery", "infer_predictions"]
