"""ProgSnapAssignmentId: o AssignmentID do dataset (ex.: 439), distinto do id do banco."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgSnapAssignmentId:
    """AssignmentID do ProgSnap2 — o id do DATASET, não o id do banco.

    Os dois são inteiros e significam coisas diferentes; confundi-los já custou uma consulta
    manual ao app.db. Como tipo distinto, passar um no lugar do outro deixa de ser um int que passa
    despercebido.
    """

    value: int

    def __post_init__(self) -> None:
        # bool é subclasse de int e passaria calado; None chegaria como "kc/assignment_None/".
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise ValueError(f"AssignmentID do ProgSnap2 precisa ser int: {self.value!r}")

    def __str__(self) -> str:
        return str(self.value)
