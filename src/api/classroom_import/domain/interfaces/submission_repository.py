"""A interface de persistência das submissões."""

from __future__ import annotations

from typing import Protocol

from api.classroom_import.domain.entities.submission_entity import Submission


class ISubmissionRepository(Protocol):
    def add(self, submission: Submission) -> int: ...
