"""Configuração mutável do treino — espelha kc_pipeline.settings.

`main()` os reescreve a partir do env e os testes os monkeypatcham. Leitores importam o módulo
e acessam `settings.DATA_ROOT`; `from ... import DATA_ROOT` congelaria o valor no import.
"""

from __future__ import annotations

from pathlib import Path

# Raiz do FS de dados; resolvida em path absoluto no main() para não depender do cwd herdado do
# web (Open Q2/A6).
DATA_ROOT = Path("data")
DB_PATH = "app.db"
