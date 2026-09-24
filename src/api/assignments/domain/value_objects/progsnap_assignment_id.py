# ProgSnapAssignmentId, o AssignmentID do dataset (por exemplo 439), distinto do id do banco.

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgSnapAssignmentId:
    # AssignmentID do ProgSnap2 (o id do dataset), tipo distinto do id do banco.

    value: int

    def __post_init__(self) -> None:
        # bool é subclasse de int e passaria calado; None chegaria como "kc/assignment_None/".
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise ValueError(f"AssignmentID do ProgSnap2 precisa ser int: {self.value!r}")

    def __str__(self) -> str:
        return str(self.value)
