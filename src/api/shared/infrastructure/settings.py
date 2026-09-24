# Configuração mutável da app layer, uma raiz de dados e um caminho de banco.
from __future__ import annotations

from pathlib import Path

# Leia sempre via `settings.DATA_ROOT`, nunca por import direto (congela o valor cedo demais).
DATA_ROOT = Path("data")

# app.db, idem, resolvido de EDMKT_DB_PATH nos subprocessos.
DB_PATH = "app.db"
