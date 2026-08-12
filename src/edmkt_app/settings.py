"""Configuração mutável da app layer: uma raiz de dados, um caminho de banco.

Antes disto, `DATA_ROOT` tinha SEIS definições — eda, features_cache, ingestion/service,
kc_pipeline, train e mastery_service, cada uma com o mesmo `Path("data")` e um comentário
dizendo que espelhava as outras. O fixture de teste do treino precisava lembrar de apontar DUAS
delas para o tmp_path; esquecer uma faria o teste escrever na árvore `data/` de verdade, sem
avisar.

**Leia sempre pelo módulo** — `settings.DATA_ROOT`, nunca `from edmkt_app.settings import
DATA_ROOT`. A segunda forma congela o valor no momento do import, e tanto o override do
`main()` (a partir do env) quanto o monkeypatch do teste deixariam de alcançar o leitor.
"""

from __future__ import annotations

from pathlib import Path

# Raiz do FS de dados: data/<turma_slug>/{raw,clean,cache,kc,models}. Os subprocessos a
# resolvem em path absoluto a partir do env (EDMKT_DATA_ROOT) para não depender do cwd herdado
# do web (Pitfall 2).
DATA_ROOT = Path("data")

# app.db — idem, resolvido de EDMKT_DB_PATH nos subprocessos.
DB_PATH = "app.db"
