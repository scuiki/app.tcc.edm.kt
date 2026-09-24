from __future__ import annotations


class NotFound(Exception):
    """O recurso alvo não existe.

    Categoria distinta de regra violada: um endpoint distingue as duas (404 contra 409). Não
    acumula com as regras: se o alvo não existe, não há sobre o que aplicar as demais.
    """
