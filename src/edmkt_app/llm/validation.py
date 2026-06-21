"""Validação por conteúdo (KC-04) + retry transiente vs falha-dura (D-04).

Duas exceções classificam o resultado do transporte:
  - TransientLLMError: rede/429/5xx/exit≠0/timeout — re-chamar PODE ajudar (retry com backoff).
  - EmptyContentError: conteúdo vazio/sem KC — re-chamar NÃO ajuda (falha-dura, sem retry inútil).

`validate_kc_result` é a checagem por CONTEÚDO (não por existência de arquivo): exige ≥1 KC, cada
um com `name`, como defesa-em-profundidade sobre o `minItems: 1` do schema. `call_with_retry`
limita o retry a N tentativas (D-04: bounda o DoS de cota da subscription).
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar


class TransientLLMError(Exception):
    """Falha transiente do transporte (rede/429/5xx/exit≠0/timeout) — retentável."""


class EmptyContentError(Exception):
    """Conteúdo vazio/inválido do LLM — falha-dura, re-chamar não ajuda (KC-04/D-04)."""


def validate_kc_result(result: dict) -> None:
    """Levanta EmptyContentError se o resultado não tem ≥1 KC nomeado (KC-04).

    `{}` / sem `kcs` / `kcs` vazia / KC sem `name` são todos conteúdo-vazio (falha-dura), não
    Q-matrix parcial — defesa-em-profundidade além do `minItems: 1` do schema.
    """
    if not result:
        raise EmptyContentError("resultado vazio do LLM")
    kcs = result.get("kcs")
    if not kcs:
        raise EmptyContentError("nenhum KC no resultado (kcs ausente ou vazia)")
    for kc in kcs:
        if not kc.get("name"):
            raise EmptyContentError("KC sem 'name' no resultado")


_T = TypeVar("_T")


def call_with_retry(
    fn: Callable[[], _T],
    retries: int = 3,
    base_delay: float = 0.5,
) -> _T:
    """Chama fn() retentando SÓ TransientLLMError com backoff exponencial, até `retries` vezes.

    EmptyContentError propaga IMEDIATAMENTE (re-chamar não muda o conteúdo → evita retry inútil
    que dreceria a cota, D-04). O sleep é `time.sleep` referenciado em runtime para o teste poder
    monkeypatchá-lo a no-op.
    """
    # WR-03: retries<1 deixaria o loop sem rodar e `raise last_exc` viraria `raise None`
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
