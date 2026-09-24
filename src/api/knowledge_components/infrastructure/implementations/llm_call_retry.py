# Como tratar a falha de uma chamada ao LLM, repetir a transiente, desistir da de conteúdo.
from __future__ import annotations

import time
from typing import Callable, TypeVar


# Falha transiente do transporte (rede/429/5xx/exit≠0/timeout), retentável.
class TransientLLMError(Exception):
    pass


# Conteúdo vazio/inválido do LLM, falha-dura, re-chamar não ajuda.
class EmptyContentError(Exception):
    pass


_T = TypeVar("_T")


def call_with_retry(
    fn: Callable[[], _T],
    retries: int = 3,
    base_delay: float = 0.5,
) -> _T:
    # Retry só de TransientLLMError com backoff, EmptyContentError sobe na hora, sem retry inútil.
    if retries < 1:
        # Guard explícito, sem ele o loop não rodaria e `raise last_exc` viraria `raise None`.
        raise ValueError(f"retries must be >= 1, got {retries}")
    last_exc: TransientLLMError | None = None
    for attempt in range(retries):
        try:
            return fn()
        except TransientLLMError as exc:
            last_exc = exc
            if attempt < retries - 1:
                # `time.sleep`, não "from time import sleep", para o teste conseguir monkeypatch.
                time.sleep(base_delay * (2**attempt))
    raise last_exc  # type: ignore[misc]  # retries>=1 garante que last_exc foi setado
