"""Os hiperparâmetros do Code-DKT, congelados no protocolo de Shi et al. (2022).

Vêm do notebook 06_code_dkt.ipynb do TCC 1 (DEFAULT_CONFIG, célula 3, e o BEST_CONFIG da grade,
célula 24). O teste de regressão é o árbitro: se o AUC do A439 sair da banda, é aqui que se olha.
"""

from __future__ import annotations

from types import MappingProxyType

# dropout=0.1 segue o protocolo congelado, NÃO o default 0.0 do notebook.
_FROZEN = {
    "R": 50,
    "max_path_length": 8,
    "max_path_width": 2,
    "node_embed_dim": 100,
    "path_embed_dim": 100,
    "hidden_dim": 128,
    "dropout": 0.1,
    "lr": 5e-4,
    "epochs": 40,
    "batch_size": 128,
    "grad_clip": 10,
    "max_len": 50,
    "seed": 42,
}

# MappingProxyType: o mapeamento público não aceita escrita.
CODE_DKT_HYPERPARAMETERS = MappingProxyType(_FROZEN)
