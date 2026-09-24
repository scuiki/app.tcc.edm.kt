# Rotas de /knowledge-components, HTTP puro, recebe, delega ao use case, devolve.
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.knowledge_components.application.use_cases.add_knowledge_component_use_case import (
    AddKnowledgeComponentUseCase,
)
from api.knowledge_components.application.use_cases.approve_knowledge_components_use_case import (
    ApproveKnowledgeComponentsUseCase,
)
from api.knowledge_components.application.dtos.edit_knowledge_components_dto import (
    AddKnowledgeComponentDTO,
    ApprovedKnowledgeComponentsDTO,
    ApproveKnowledgeComponentsDTO,
    KnowledgeComponentDTO,
    MergedKnowledgeComponentsDTO,
    MergeKnowledgeComponentsDTO,
    ProblemKnowledgeComponentDTO,
    RemovedKnowledgeComponentDTO,
    RemovedProblemKnowledgeComponentDTO,
    RemoveKnowledgeComponentDTO,
    RenameKnowledgeComponentBody,
    RenameKnowledgeComponentDTO,
)
from api.knowledge_components.application.dtos.get_kc_generation_job_dto import (
    KnowledgeComponentGenerationJobDTO,
)
from api.knowledge_components.application.dtos.list_knowledge_components_dto import (
    ListKnowledgeComponentsResponseDTO,
)
from api.knowledge_components.application.use_cases.list_knowledge_components_use_case import (
    ListKnowledgeComponentsUseCase,
)
from api.knowledge_components.application.use_cases.get_kc_generation_job_use_case import (
    GetKnowledgeComponentGenerationJobUseCase,
)
from api.knowledge_components.application.use_cases.merge_knowledge_components_use_case import (
    MergeKnowledgeComponentsUseCase,
)
from api.knowledge_components.application.use_cases.remove_knowledge_component_use_case import (
    RemoveKnowledgeComponentUseCase,
)
from api.knowledge_components.application.use_cases.rename_knowledge_component_use_case import (
    RenameKnowledgeComponentUseCase,
)
from api.knowledge_components.application.dtos.start_kc_generation_dto import (
    StartedJobDTO,
    StartKnowledgeComponentGenerationDTO,
)
from api.knowledge_components.application.use_cases.start_kc_generation_use_case import (
    StartKnowledgeComponentGenerationUseCase,
)
from api.knowledge_components.application.use_cases.add_problem_knowledge_component_use_case import (
    AddProblemKnowledgeComponentUseCase,
)
from api.knowledge_components.application.use_cases.remove_problem_knowledge_component_use_case import (
    RemoveProblemKnowledgeComponentUseCase,
)
from api.knowledge_components.presentation import dependencies

router = APIRouter(prefix="/knowledge-components", tags=["knowledge_components"])


@router.get(
    "",
    response_model=ListKnowledgeComponentsResponseDTO,
    description="Os KCs do assignment, cada um com os problemas a que ele se liga.",
)
def list_knowledge_components(
    assignment_id: int,
    use_case: ListKnowledgeComponentsUseCase = Depends(
        dependencies.list_knowledge_components_use_case
    ),
) -> ListKnowledgeComponentsResponseDTO:
    return use_case.execute(assignment_id)


@router.post("/generation-jobs", status_code=202, response_model=StartedJobDTO)
def start_kc_generation(
    body: StartKnowledgeComponentGenerationDTO,
    use_case: StartKnowledgeComponentGenerationUseCase = Depends(
        dependencies.start_kc_generation_use_case
    ),
) -> StartedJobDTO:
    return use_case.execute(body)


@router.get("/generation-jobs/{job_id}", response_model=KnowledgeComponentGenerationJobDTO)
def get_kc_generation_job(
    job_id: int,
    use_case: GetKnowledgeComponentGenerationJobUseCase = Depends(
        dependencies.get_kc_generation_job_use_case
    ),
) -> KnowledgeComponentGenerationJobDTO:
    return use_case.execute(job_id)


@router.post("", status_code=201, response_model=KnowledgeComponentDTO)
def add_knowledge_component(
    body: AddKnowledgeComponentDTO,
    use_case: AddKnowledgeComponentUseCase = Depends(dependencies.add_knowledge_component_use_case),
) -> KnowledgeComponentDTO:
    return use_case.execute(body)


@router.patch("/{kc_id}", response_model=KnowledgeComponentDTO)
def rename_knowledge_component(
    kc_id: int,
    body: RenameKnowledgeComponentBody,
    use_case: RenameKnowledgeComponentUseCase = Depends(
        dependencies.rename_knowledge_component_use_case
    ),
) -> KnowledgeComponentDTO:
    return use_case.execute(RenameKnowledgeComponentDTO(kc_id=kc_id, name=body.name))


@router.delete("/{kc_id}", response_model=RemovedKnowledgeComponentDTO)
def remove_knowledge_component(
    kc_id: int,
    use_case: RemoveKnowledgeComponentUseCase = Depends(
        dependencies.remove_knowledge_component_use_case
    ),
) -> RemovedKnowledgeComponentDTO:
    return use_case.execute(RemoveKnowledgeComponentDTO(kc_id=kc_id))


@router.post("/merge", response_model=MergedKnowledgeComponentsDTO)
def merge_knowledge_components(
    body: MergeKnowledgeComponentsDTO,
    use_case: MergeKnowledgeComponentsUseCase = Depends(
        dependencies.merge_knowledge_components_use_case
    ),
) -> MergedKnowledgeComponentsDTO:
    return use_case.execute(body)


@router.post("/approve", response_model=ApprovedKnowledgeComponentsDTO)
def approve_knowledge_components(
    body: ApproveKnowledgeComponentsDTO,
    use_case: ApproveKnowledgeComponentsUseCase = Depends(dependencies.approve_knowledge_components_use_case),
) -> ApprovedKnowledgeComponentsDTO:
    return use_case.execute(body)


@router.post(
    "/{kc_id}/problems/{problem_id}",
    status_code=201,
    response_model=ProblemKnowledgeComponentDTO,
    description="Liga um KC que já existe a mais um problema do mesmo assignment.",
)
def add_problem_knowledge_component(
    kc_id: int,
    problem_id: int,
    use_case: AddProblemKnowledgeComponentUseCase = Depends(
        dependencies.add_problem_knowledge_component_use_case
    ),
) -> ProblemKnowledgeComponentDTO:
    return use_case.execute(ProblemKnowledgeComponentDTO(kc_id=kc_id, problem_id=problem_id))


@router.delete(
    "/{kc_id}/problems/{problem_id}",
    response_model=RemovedProblemKnowledgeComponentDTO,
    description="Tira o KC de um problema só; se ele perder o último problema, sai junto.",
)
def remove_problem_knowledge_component(
    kc_id: int,
    problem_id: int,
    use_case: RemoveProblemKnowledgeComponentUseCase = Depends(
        dependencies.remove_problem_knowledge_component_use_case
    ),
) -> RemovedProblemKnowledgeComponentDTO:
    return use_case.execute(ProblemKnowledgeComponentDTO(kc_id=kc_id, problem_id=problem_id))
