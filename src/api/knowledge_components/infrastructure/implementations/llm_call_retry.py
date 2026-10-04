# Como tratar a falha de uma chamada ao LLM, repetir a transiente e a resposta inválida.
from __future__ import annotations

import time
from typing import Callable, TypeVar

from ml.kc_generation.llm_client import InvalidLLMResponseError


# Falha transiente do transporte (rede/429/5xx/exit≠0/timeout), retentável.
class TransientLLMError(Exception):
    pass


_T = TypeVar("_T")


def call_with_retry(
    fn: Callable[[], _T],
    retries: int = 3,
    base_delay: float = 0.5,
) -> _T:
    # Erro transiente e resposta inválida são pedidos de novo com espera, `retries` vezes ao todo
    if retries < 1:
        # Guard explícito, sem ele o loop não rodaria e `raise last_exc` viraria `raise None`.
        raise ValueError(f"retries must be >= 1, got {retries}")
    last_exc: TransientLLMError | InvalidLLMResponseError | None = None
    for attempt in range(retries):
        try:
            return fn()
        except (TransientLLMError, InvalidLLMResponseError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                # `time.sleep`, não "from time import sleep", para o teste conseguir monkeypatch.
                time.sleep(base_delay * (2**attempt))
    raise last_exc  # type: ignore[misc]  # retries>=1 garante que last_exc foi setado
