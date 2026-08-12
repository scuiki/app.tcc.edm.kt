"""Configuração mutável do KC-gen: os únicos globais do pacote, num lugar só.

`main()` os reescreve a partir do env e os testes os monkeypatcham. Ficam isolados aqui em vez
de espalhados pelos módulos porque quem lê tem de ver o valor CORRENTE — os leitores importam o
módulo e acessam `settings.DATA_ROOT`, nunca `from ... import DATA_ROOT`, que congelaria o valor
no momento do import.
"""

from __future__ import annotations

from pathlib import Path

# Raiz do FS de dados; resolvida em path absoluto no main() para não depender do cwd herdado do
# web (Pitfall 2).
DATA_ROOT = Path("data")
DB_PATH = "app.db"

# Modelo congelado do TCC 1 (D-01/A4): id pinado, não o alias `haiku`, para fidelidade científica.
MODEL_ID = "claude-haiku-4-5-20251001"
