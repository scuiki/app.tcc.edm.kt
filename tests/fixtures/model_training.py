# Fixtures de model_training, e o modelo minúsculo que o dashboard também usa.

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest
import torch

from api.assignments.domain.entities.assignment_entity import Assignment
from api.assignments.domain.entities.classroom_entity import Classroom
from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId
from api.assignments.infrastructure.repositories.sqlite_assignment_repository import (
    SqliteAssignmentRepository,
)
from api.assignments.infrastructure.repositories.sqlite_classroom_repository import (
    SqliteClassroomRepository,
)
from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent
from api.knowledge_components.domain.entities.qmatrix_binding_entity import QMatrixBinding
from api.knowledge_components.infrastructure.repositories.sqlite_knowledge_component_repository import (
    SqliteKnowledgeComponentRepository,
)
from api.knowledge_components.infrastructure.repositories.sqlite_qmatrix_repository import (
    SqliteQMatrixRepository,
)
from api.model_training.domain.value_objects.training_dataset import TrainingDataset
from api.model_training.domain.value_objects.training_outcome import TrainingOutcome
from api.model_training.infrastructure.implementations.trained_model_file_store import (
    TrainedModelFileStore,
)
from api.model_training.infrastructure.repositories.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from ml.code_dkt.model import CodeDKTModel
from ml.reproducibility.random_seed import seed_all_random_generators
from tests.fixtures.sample_data import (
    JAVA_BAD,
    JAVA_EMPTY_CLASS,
    JAVA_OK_A,
    JAVA_OK_B,
    JAVA_OK_C,
)


@pytest.fixture
def java_snippets() -> SimpleNamespace:
    return SimpleNamespace(
        ok_a=JAVA_OK_A, ok_b=JAVA_OK_B, ok_c=JAVA_OK_C, bad=JAVA_BAD, empty_class=JAVA_EMPTY_CLASS
    )


@pytest.fixture
def tiny_model() -> torch.nn.Module:
    # Não é o Code-DKT, só tem os dois atributos de que a releitura do modelo precisa
    class _TinyModel(torch.nn.Module):
        def __init__(self, input_dim: int = 3, output_dim: int = 2):
            super().__init__()
            self.input_dim = input_dim
            self.fc = torch.nn.Linear(input_dim, output_dim)

    return _TinyModel()


@pytest.fixture
def tiny_vocab() -> dict:
    return {
        "token_to_idx": {"<PAD>": 0, "<UNK>": 1, "if": 2, "return": 3},
        "path_to_idx": {"<PAD>": 0, "<UNK>": 1, "a->b": 2},
        "node_count": 4,
        "path_count": 3,
    }


@pytest.fixture
def tiny_config() -> dict:
    return {"hidden_dim": 8, "dropout": 0.1, "R": 4, "node_embed_dim": 6, "path_embed_dim": 6}


@pytest.fixture
def cache_config() -> dict:
    # Os parâmetros de extração de paths de Shi et al. 2022
    return {"max_path_length": 8, "max_path_width": 2, "R": 50, "seed": 42}


@pytest.fixture
def cache_code_states() -> dict[str, str]:
    # Um snapshot de cada caso de parse, com paths, sem paths, com falha e vazio
    return {
        "c_ok1": JAVA_OK_A,
        "c_ok2": JAVA_OK_B,
        "c_empty": JAVA_EMPTY_CLASS,
        "c_bad": JAVA_BAD,
        "c_blank": "   ",
    }


@pytest.fixture
def trained_artifact(tmp_db, data_root, tiny_vocab, tiny_config):
    # Code-DKT minúsculo publicado, sem treino, e uma Q-matrix em que o problema 3 liga os 2 KCs
    conn = tmp_db
    now = "2026-06-21T00:00:00Z"

    classroom_id = SqliteClassroomRepository(conn).add(
        Classroom(id=None, name="Turma 6", created_at=now)
    )
    assignment_id = SqliteAssignmentRepository(conn).add(
        Assignment(
            id=None,
            classroom_id=classroom_id,
            name="A439",
            progsnap_assignment_id=439,
            published_model_id=None,
            created_at=now,
            status="kc_approved",
        )
    )

    seed_all_random_generators(42, strict=False)
    problem_count = 3
    model = CodeDKTModel(
        input_dim=2 * problem_count,
        hidden_dim=tiny_config["hidden_dim"],
        output_dim=problem_count,
        node_count=tiny_vocab["node_count"],
        path_count=tiny_vocab["path_count"],
        dropout=tiny_config["dropout"],
        R=tiny_config["R"],
        node_embed_dim=tiny_config["node_embed_dim"],
        path_embed_dim=tiny_config["path_embed_dim"],
    )

    store = TrainedModelFileStore(conn)
    artifact_id = store.save(
        TrainingDataset(
            events=pd.DataFrame(),
            classroom_slug=ClassroomSlug.from_name("Turma 6"),
            progsnap_assignment_id=ProgSnapAssignmentId(439),
            classroom_id=classroom_id,
        ),
        assignment_id,
        TrainingOutcome(
            model=model, vocab=tiny_vocab, hyperparameters=tiny_config,
            first_attempt_auc=None, java_parse_rate=1.0,
        ),
    )
    trained_model = SqliteTrainedModelRepository(conn).get(artifact_id)
    SqliteAssignmentRepository(conn).set_published_model(assignment_id, artifact_id)

    kc_repo = SqliteKnowledgeComponentRepository(conn)
    kc1 = kc_repo.add(
        KnowledgeComponent(id=None, assignment_id=assignment_id, name="Laços", group_index=0)
    )
    kc2 = kc_repo.add(
        KnowledgeComponent(id=None, assignment_id=assignment_id, name="Condicionais", group_index=1)
    )
    qm_repo = SqliteQMatrixRepository(conn)
    for kc_id, problem_id in [(kc1, 1), (kc1, 3), (kc2, 2), (kc2, 3)]:
        qm_repo.add(
            QMatrixBinding(id=None, assignment_id=assignment_id, kc_id=kc_id, problem_id=problem_id)
        )

    return SimpleNamespace(
        conn=conn,
        classroom_id=classroom_id,
        assignment_id=assignment_id,
        artifact_id=artifact_id,
        version_number=trained_model.version_number,
        artifact_dir=trained_model.model_dir,
        trained_model=trained_model,
        kcs=kc_repo.list_by_assignment(assignment_id),
        qmatrix=qm_repo.list_by_assignment(assignment_id),
        store=store,
        model=model,
        vocab=tiny_vocab,
        config=tiny_config,
    )
