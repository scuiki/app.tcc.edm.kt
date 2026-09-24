"""Os pedidos e as respostas das edições da Q-matrix pelo professor."""

from __future__ import annotations

from pydantic import BaseModel

from api.assignments.domain.assignment_entity import AssignmentStatus


class AddKnowledgeComponentDTO(BaseModel):
    assignment_id: int
    name: str
    problem_ids: list[int] = []  # os problemas que o novo KC já liga (opcional)


class RenameKnowledgeComponentBody(BaseModel):
    """O corpo do PATCH; o kc_id vem do caminho e é juntado no controller."""

    name: str


class RenameKnowledgeComponentDTO(BaseModel):
    kc_id: int
    name: str


class RemoveKnowledgeComponentDTO(BaseModel):
    kc_id: int


class MergeKnowledgeComponentsDTO(BaseModel):
    assignment_id: int
    keep_kc_id: int  # o KC que fica
    drop_kc_id: int  # o KC que some: seus problemas passam para keep_kc_id


class ApproveQMatrixDTO(BaseModel):
    assignment_id: int


class KnowledgeComponentDTO(BaseModel):
    id: int
    name: str


class RemovedKnowledgeComponentDTO(BaseModel):
    deleted_kc_id: int


class MergedKnowledgeComponentsDTO(BaseModel):
    keep_kc_id: int
    drop_kc_id: int


class ApprovedQMatrixDTO(BaseModel):
    assignment_id: int
    status: AssignmentStatus
