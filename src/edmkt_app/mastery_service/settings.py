"""Raiz do FS de dados do mastery: o único global mutável do pacote.

Isolado aqui pelo mesmo motivo de kc_pipeline.settings — quem lê importa o módulo e acessa
`settings.DATA_ROOT`, nunca `from ... import DATA_ROOT`, que congelaria o valor no import e
quebraria o override de teste/deploy.
"""

from __future__ import annotations

from pathlib import Path

DATA_ROOT = Path("data")
