"""Glue público do edmkt_core: DataFrame de entrada, artefatos de saída.

NÃO é um port do TCC 1 — é código autoral desta aplicação (D-01), diferente de `features.py`,
`models/code_dkt.py` e `kc/generation.py`, que carregam a linha `Ported from tcc.edm.kt` e
ficam inteiros de propósito, para seguirem diffáveis 1:1 contra a referência.

Divisão: `partitioning` (split por aluno + vocab train-only, CORE-04) · `training` (a ordem
load-bearing de train_and_evaluate). Os nomes seguem reexportados — divisão de arquivo, não de
contrato.
"""

from edmkt_core.pipeline.partitioning import build_train_vocab, split_by_subject
from edmkt_core.pipeline.training import code_state_ids, code_states_from_df, train_and_evaluate

__all__ = [
    "build_train_vocab",
    "code_state_ids",
    "code_states_from_df",
    "split_by_subject",
    "train_and_evaluate",
]
