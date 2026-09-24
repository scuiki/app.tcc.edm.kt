"""O corpo do worker de geração de KCs: gera, valida tudo, e só então grava tudo junto.

Roda no subprocess, sob a trava de job (quem a pega é o worker). O retorno se perde com o
subprocess: o que sobrevive é o que fica gravado nas linhas do job, dos KCs e da Q-matrix.
"""

from __future__ import annotations

from api.assignments.domain.entities.assignment_entity import AssignmentStatus
from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.interfaces.classroom_repository import IClassroomRepository
from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId
from api.classroom_import.domain.interfaces.cleaned_submissions_store import ICleanedSubmissionsStore
from api.knowledge_components.domain.kc_generation_job_repository import (
    KnowledgeComponentGenerationJobRepository,
)
from api.knowledge_components.domain.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.knowledge_component_generator import (
    KnowledgeComponentGenerator,
)
from api.knowledge_components.domain.knowledge_component_repository import (
    KnowledgeComponentRepository,
)
from api.knowledge_components.domain.qmatrix_binding_entity import QMatrixBinding
from api.knowledge_components.domain.qmatrix_repository import QMatrixRepository
from api.shared.application.services.clock import utc_now_iso
from api.shared.application.interfaces.unit_of_work import IUnitOfWork


class RunKnowledgeComponentGenerationUseCase:
    def __init__(
        self,
        assignments: IAssignmentRepository,
        classrooms: IClassroomRepository,
        cleaned_submissions: ICleanedSubmissionsStore,
        generator: KnowledgeComponentGenerator,
        knowledge_components: KnowledgeComponentRepository,
        qmatrix: QMatrixRepository,
        jobs: KnowledgeComponentGenerationJobRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._assignments = assignments
        self._classrooms = classrooms
        self._cleaned_submissions = cleaned_submissions
        self._generator = generator
        self._knowledge_components = knowledge_components
        self._qmatrix = qmatrix
        self._jobs = jobs
        self._unit_of_work = unit_of_work

    def execute(self, assignment_id: int, job_id: int) -> dict:
        assignment = self._assignments.get(assignment_id)
        if assignment is None:
            raise ValueError(f"assignment {assignment_id} inexistente")
        classroom = self._classrooms.get(assignment.classroom_id)
        slug = ClassroomSlug.from_name(classroom.name)
        progsnap_id = ProgSnapAssignmentId(assignment.progsnap_assignment_id)

        self._jobs.mark_running(job_id, started_at=utc_now_iso())
        generated = self._generator.generate(
            self._cleaned_submissions.read(slug, progsnap_id),
            slug,
            progsnap_id,
            on_stage=lambda stage: self._jobs.update_stage(job_id, stage, utc_now_iso()),
        )
        # Validar tudo, depois gravar: um problema sem KC reprova a Q-matrix inteira, antes de
        # abrir a transação. O job falha e nada parcial é gravado.
        generated.ensure_every_problem_has_a_kc()

        with self._unit_of_work:
            kc_id_of_group = {
                group: self._knowledge_components.add(
                    KnowledgeComponent(
                        id=None,
                        assignment_id=assignment_id,
                        name=generated.group_names[group],
                        group_index=group,
                    )
                )
                for group in sorted(generated.group_names)
            }
            for problem_id in generated.problem_ids:
                for group in generated.groups_by_problem[problem_id]:
                    self._qmatrix.add(
                        QMatrixBinding(
                            id=None,
                            assignment_id=assignment_id,
                            kc_id=kc_id_of_group[group],
                            problem_id=problem_id,
                        )
                    )
            # O status e a conclusão do job na MESMA transação dos KCs: nunca um assignment em
            # kc_draft com o job marcado como failed.
            self._assignments.set_status(assignment_id, AssignmentStatus.KC_DRAFT)
            self._jobs.mark_done(job_id, updated_at=utc_now_iso())

        return {"n_groups": len(generated.group_names), "n_problems": len(generated.problem_ids)}
