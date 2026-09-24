from __future__ import annotations


class NotFound(Exception):
    # Categoria distinta de regra violada (404 contra 409); não acumula com as demais regras.
    pass
