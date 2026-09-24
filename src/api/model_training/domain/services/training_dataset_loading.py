"""Monta o dado que treino e inferência consomem (TrainingDataset): o dado limpo do assignment,
só com Run.Program.

Este é o único lugar que monta esse recorte. Antes, o treino e a inferência liam o Parquet cada um
por si; os dois esqueceram o recorte, o modelo treinou sobre 57,6% de eventos rotulados como erro e
o first-attempt AUC caiu para 0,6959, fora da banda. Quem modela passa a receber o dado pronto.
"""

from __future__ import annotations

from api.assignments.domain.interfaces.assignment_repository import IAssignmentRepository
from api.assignments.domain.interfaces.classroom_repository import IClassroomRepository
from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId
from api.classroom_import.domain.interfaces.cleaned_submissions_store import ICleanedSubmissionsStore
from api.classroom_import.domain.services.submission_event import keep_only_program_runs

from api.model_training.domain.value_objects.training_dataset import TrainingDataset


def load_training_dataset(
    assignment_id: int,
    assignments: IAssignmentRepository,
    classrooms: IClassroomRepository,
    cleaned_submissions: ICleanedSubmissionsStore,
) -> TrainingDataset:
    """assignment (id do banco) → turma → Parquet limpo → recorte Run.Program."""
    assignment = assignments.get(assignment_id)
    if assignment is None:
        raise ValueError(f"assignment {assignment_id} inexistente")
    classroom = classrooms.get(assignment.classroom_id)
    if classroom is None:
        # Turma órfã (a FK é por conexão): erro nomeado em vez de AttributeError em .name.
        raise ValueError(f"turma {assignment.classroom_id} inexistente")

    slug = ClassroomSlug.from_name(classroom.name)
    progsnap_id = ProgSnapAssignmentId(assignment.progsnap_assignment_id)
    return TrainingDataset(
        events=keep_only_program_runs(cleaned_submissions.read(slug, progsnap_id)),
        classroom_slug=slug,
        progsnap_assignment_id=progsnap_id,
        classroom_id=assignment.classroom_id,
    )
