# Hiperparâmetros do Code-DKT (Shi et al. 2022), congelados; do notebook 06_code_dkt.ipynb, TCC 1.

from __future__ import annotations

from types import MappingProxyType

# dropout=0.1 segue o protocolo congelado, NÃO o default 0.0 do notebook.
_FROZEN = {
    "R": 100,
    # Separada da seed do treino, para a amostra de paths de cada solução não mudar entre execuções
    "path_sampling_seed": 42,
    "max_path_length": 8,
    "max_path_width": 2,
    "node_embed_dim": 100,
    "path_embed_dim": 100,
    "hidden_dim": 128,
    "dropout": 0.1,
    "lr": 5e-4,
    "epochs": 40,
    "batch_size": 128,
    # O lote de 128 passa em pedaços de 64 alunos, porque com R=100 ele inteiro não cabe na GPU
    "batch_chunk_size": 64,
    "grad_clip": 10,
    "max_len": 50,
    "seed": 42,
}

# MappingProxyType garante que o mapeamento público não aceita escrita.
CODE_DKT_HYPERPARAMETERS = MappingProxyType(_FROZEN)
