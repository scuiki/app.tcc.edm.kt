"""Value objects da app layer: uma invariante por tipo, construída na fronteira.

Cada tipo aqui absorve uma checagem que o código repetia. `TurmaSlug` substitui as 7 definições
de `_slug`; `ProgSnapAssignmentId`, as 5 de `_progsnap_aid`; `CodeStateId`, o `_safe_csid_name`;
`ConfinedPath`, o `_confine` (e, no passo do ArtifactStore, os dois espelhos dele lá).

Regra de fronteira: o VO é construído e validado AQUI, na app layer, e desembrulhado para
primitivo antes de entrar em qualquer função de `edmkt_core` — a camada científica é congelada
para a banca e não conhece estes tipos.

Todos são `frozen`: um valor validado não muda depois de construído; para ter outro, construa
outro. `__fspath__` deixa os que são componentes de caminho serem usados direto em `Path / x`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_SLUG_FALLBACK = "turma"
# Nome de arquivo do cache de paths: alfanumérico + . _ - e nada mais. Fecha separador de
# caminho, NUL e qualquer coisa que o FS interprete.
_CSID_ALLOWED = re.compile(r"[A-Za-z0-9._-]+")


@dataclass(frozen=True)
class TurmaSlug:
    """Componente de diretório derivado do nome de turma que o professor digitou.

    O nome é entrada arbitrária; o slug é a ÚNICA forma dele que vira caminho. Nunca usar o
    nome cru como diretório (T-03-15).
    """

    value: str

    @classmethod
    def from_name(cls, name: str) -> "TurmaSlug":
        # Idempotente por construção: "-" também cai no [^a-z0-9], então re-slugificar um slug
        # devolve ele mesmo — aplicar duas vezes por engano não corrompe o caminho.
        s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
        return cls(s or _SLUG_FALLBACK)

    def __str__(self) -> str:
        return self.value

    def __fspath__(self) -> str:
        return self.value


@dataclass(frozen=True)
class CodeStateId:
    """CodeStateID do ProgSnap2 que vira NOME DE ARQUIVO no cache de features.

    Único ponto do projeto em que um identificador vindo do dataset do professor é usado como
    caminho, então a validação é de admissão: aceita a forma conhecida e rejeita todo o resto,
    em vez de tentar limpar (T-04-CSID).
    """

    value: str

    def __post_init__(self) -> None:
        if ".." in self.value or not _CSID_ALLOWED.fullmatch(self.value):
            raise ValueError(f"CodeStateID inseguro para nome de arquivo: {self.value!r}")

    def __str__(self) -> str:
        return self.value

    def __fspath__(self) -> str:
        return self.value


@dataclass(frozen=True)
class ConfinedPath:
    """Caminho provado como estando sob `root`, pela disciplina resolve-depois-confere.

    Confere o caminho JÁ resolvido, não a string: `..` e symlink são fechados antes da
    comparação, e um `..` que volta para dentro segue legítimo. Construir este tipo É a prova —
    quem recebe um `ConfinedPath` não precisa reconferir.
    """

    path: Path
    root: Path

    def __post_init__(self) -> None:
        resolved_root = Path(self.root).resolve()
        resolved = Path(self.path).resolve()
        if resolved != resolved_root and resolved_root not in resolved.parents:
            raise ValueError(f"caminho fora da raiz permitida: {resolved} não está sob {resolved_root}")

    def __fspath__(self) -> str:
        return str(Path(self.path).resolve())

    def __str__(self) -> str:
        return self.__fspath__()


@dataclass(frozen=True)
class ProgSnapAssignmentId:
    """AssignmentID do ProgSnap2 — o id do DATASET, não o id do banco.

    Os dois são inteiros e significam coisas diferentes; confundi-los custou uma consulta manual
    ao app.db na UAT da Fase 4 (backlog 999.2). Como tipo distinto, passar um no lugar do outro
    para de ser um int que passa despercebido.
    """

    value: int

    @classmethod
    def from_name(cls, assignment_name: str) -> "ProgSnapAssignmentId":
        m = re.search(r"(\d+)", assignment_name)
        if m is None:
            raise ValueError(f"AssignmentID não derivável do nome: {assignment_name!r}")
        return cls(int(m.group(1)))

    def __str__(self) -> str:
        return str(self.value)
