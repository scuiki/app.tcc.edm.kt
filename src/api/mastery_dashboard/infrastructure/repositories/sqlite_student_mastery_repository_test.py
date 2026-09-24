"""SqliteStudentMasteryRepository: a matriz aluno × KC gravada por versão de modelo."""

from __future__ import annotations

from api.mastery_dashboard.domain.entities.student_mastery_entity import StudentMastery
from api.mastery_dashboard.infrastructure.repositories.sqlite_student_mastery_repository import (
    SqliteStudentMasteryRepository,
)


def test_masteries_round_trip_per_model(tmp_db):
    classroom_id = tmp_db.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('T', 't0');"
    ).lastrowid
    assignment_id = tmp_db.execute(
        "INSERT INTO assignment (classroom_id, name, created_at) VALUES (?, 'A', 't0');",
        (classroom_id,),
    ).lastrowid
    kc_id = tmp_db.execute(
        "INSERT INTO kc (assignment_id, name) VALUES (?, 'laços');", (assignment_id,)
    ).lastrowid
    model_id = tmp_db.execute(
        "INSERT INTO model_artifact (assignment_id, version_number, content_hash, artifact_dir, "
        "created_at) VALUES (?, 1, 'h', 'v1', 't0');",
        (assignment_id,),
    ).lastrowid
    repository = SqliteStudentMasteryRepository(tmp_db)

    mastery_id = repository.add(
        StudentMastery(id=None, trained_model_id=model_id, student_id="S1", kc_id=kc_id, mastery=0.75)
    )

    assert repository.count_by_model(model_id) == 1
    assert repository.list_by_model(model_id) == [
        StudentMastery(id=mastery_id, trained_model_id=model_id, student_id="S1", kc_id=kc_id, mastery=0.75)
    ]
    assert repository.count_by_model(model_id + 1) == 0
