"""A interface de persistência da matriz aluno × KC, materializada uma vez por versão de modelo."""

from __future__ import annotations

from typing import Protocol

from api.mastery_dashboard.domain.entities.student_mastery_entity import StudentMastery


class IStudentMasteryRepository(Protocol):
    def add(self, student_mastery: StudentMastery) -> int: ...

    def count_by_model(self, trained_model_id: int) -> int: ...

    def list_by_model(self, trained_model_id: int) -> list[StudentMastery]: ...
