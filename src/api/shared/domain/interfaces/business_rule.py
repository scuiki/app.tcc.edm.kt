"""Uma regra de negócio: devolve a mensagem de recusa, ou None se o pedido passa.

As regras de um use case rodam TODAS e as recusas se acumulam (ver WriteUseCase). O contrato que
isso impõe a quem escreve uma regra: **ela não pode assumir que outra passou**. Uma regra que
dependa de "o assignment existe" busca o assignment ela mesma e tolera a ausência.

A regra recebe no construtor as interfaces de repositório de que precisa; `check` recebe só o DTO.
"""

from __future__ import annotations

from typing import Any, Protocol


class IBusinessRule(Protocol):
    def check(self, dto: Any) -> str | None: ...
