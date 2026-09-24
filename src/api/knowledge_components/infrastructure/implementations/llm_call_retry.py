"""Como tratar a falha de uma chamada ao LLM: repetir a transiente, desistir da de conteúdo.

- TransientLLMError: rede, 429, 5xx, exit≠0, timeout. Repetir PODE ajudar (retry com backoff).
- EmptyContentError: conteúdo vazio ou inválido. Repetir NÃO ajuda: falha dura, sem gastar cota.

O número de tentativas é limitado: é o que limita o gasto de cota da assinatura numa falha.
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar


class TransientLLMError(Exception):
    """Falha transiente do transporte (rede/429/5xx/exit≠0/timeout) — retentável."""


class EmptyContentError(Exception):
    """Conteúdo vazio/inválido do LLM — falha-dura, re-chamar não ajuda."""


_T = TypeVar("_T")


def call_with_retry(
    fn: Callable[[], _T],
    retries: int = 3,
    base_delay: float = 0.5,
) -> _T:
    """Chama fn() retentando SÓ TransientLLMError com backoff exponencial, até `retries` vezes.

    EmptyContentError propaga IMEDIATAMENTE (re-chamar não muda o conteúdo → evita retry inútil
    que dreceria a cota). O sleep é `time.sleep` referenciado em runtime para o teste poder
    monkeypatchá-lo a no-op.
    """
    # retries<1 deixaria o loop sem rodar e `raise last_exc` viraria `raise None`
    # (TypeError opaco). Guard explícito antes de tentar.
    if retries < 1:
        raise ValueError(f"retries must be >= 1, got {retries}")
    last_exc: TransientLLMError | None = None
    for attempt in range(retries):
        try:
            return fn()
        except TransientLLMError as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(base_delay * (2**attempt))
    raise last_exc  # type: ignore[misc]  # retries>=1 garante que last_exc foi setado
