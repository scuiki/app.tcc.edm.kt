"""A interface de persistência das submissões."""

from __future__ import annotations

from typing import Protocol

from api.classroom_import.domain.submission_entity import Submission


class SubmissionRepository(Protocol):
    def add(self, submission: Submission) -> int: ...
