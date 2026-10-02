# Hiperparâmetros do Code-DKT (Shi et al. 2022 e repositório oficial), fixos para toda turma.

from __future__ import annotations

from types import MappingProxyType

_FROZEN = {
    "R": 100,
    # Separada da seed do treino, para a amostra de paths de cada solução não mudar entre execuções
    "path_sampling_seed": 42,
    "max_path_length": 8,
    "max_path_width": 2,
    "node_embed_dim": 100,
    "path_embed_dim": 100,
    "hidden_dim": 128,
    "lr": 5e-4,
    "epochs": 40,
    "batch_size": 128,
    # O lote de 128 usa acumulação de gradiente em batches de 64, porque com R=100 não cabe na GPU
    "batch_chunk_size": 64,
    "max_len": 50,
    "seed": 42,
}

# MappingProxyType garante que o mapeamento público não aceita escrita.
CODE_DKT_HYPERPARAMETERS = MappingProxyType(_FROZEN)
