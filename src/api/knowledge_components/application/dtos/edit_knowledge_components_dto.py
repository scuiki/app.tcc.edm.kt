# Pedidos e respostas das edições que o professor faz nos KCs.
from __future__ import annotations

from pydantic import BaseModel

from api.assignments.domain.entities.assignment_entity import AssignmentStatus


class AddKnowledgeComponentDTO(BaseModel):
    assignment_id: int
    name: str
    problem_ids: list[int] = []  # os problemas que o novo KC já liga (opcional)


# O corpo do PATCH; o kc_id vem do caminho e é juntado no controller.
class RenameKnowledgeComponentBody(BaseModel):
    name: str


class RenameKnowledgeComponentDTO(BaseModel):
    kc_id: int
    name: str


class RemoveKnowledgeComponentDTO(BaseModel):
    kc_id: int


class MergeKnowledgeComponentsDTO(BaseModel):
    assignment_id: int
    keep_kc_id: int  # o KC que fica
    drop_kc_id: int  # o KC que some, seus problemas passam para keep_kc_id


class ApproveKnowledgeComponentsDTO(BaseModel):
    assignment_id: int


class KnowledgeComponentDTO(BaseModel):
    id: int
    name: str


class RemovedKnowledgeComponentDTO(BaseModel):
    deleted_kc_id: int


class ProblemKnowledgeComponentDTO(BaseModel):
    kc_id: int
    problem_id: int  # o ProblemID do dataset


class RemovedProblemKnowledgeComponentDTO(BaseModel):
    kc_id: int
    problem_id: int
    knowledge_component_removed: bool  # o KC perdeu o último problema e saiu junto


class MergedKnowledgeComponentsDTO(BaseModel):
    keep_kc_id: int
    drop_kc_id: int


class ApprovedKnowledgeComponentsDTO(BaseModel):
    assignment_id: int
    status: AssignmentStatus
