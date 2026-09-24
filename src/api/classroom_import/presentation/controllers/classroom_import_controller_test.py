# POST /classroom-imports e /classroom-imports/process pelo HTTP, herméticos via api_client.

from __future__ import annotations

import io
import zipfile

from api.classroom_import.presentation.controllers import classroom_import_controller
from api.classroom_import.presentation.dependencies import import_classroom_dataset_use_case
from api.shared.infrastructure import settings
from tests.fixtures.job_lock import lock_holder_pid

_MAIN_TABLE = (
    "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp\n"
    "S1,439,1,c1,Run.Program,0.0,2019-03-01T08:00:00Z\n"
    "S1,439,2,c2,Run.Program,1.0,2019-03-01T08:01:00Z\n"
    "S2,439,1,c3,Run.Program,1.0,2019-03-01T08:02:00Z\n"
    "S2,439,2,c4,Run.Program,0.5,2019-03-01T08:03:00Z\n"
)
_CODE_STATES = (
    "CodeStateID,Code\n"
    'c1,"public int f(){return 0;}"\n'
    'c2,"public int g(){return 1;}"\n'
    'c3,"public int h(){return 1;}"\n'
    'c4,"public int k(){return 2;}"\n'
)


def _zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("MainTable.csv", _MAIN_TABLE)
        zf.writestr("CodeStates/CodeStates.csv", _CODE_STATES)
    return buffer.getvalue()


def _upload(client):
    return client.post(
        "/classroom-imports",
        data={"classroom_name": "Turma X"},
        files={"file": ("upload.zip", _zip_bytes(), "application/zip")},
    )


def test_upload_lists_the_main_tables_without_taking_the_lock(api_client):
    client, conn = api_client

    response = _upload(client)

    assert response.status_code == 200
    body = response.json()
    assert body["classroom_slug"] == "turma-x"
    assert body["main_tables"]  # achou ao menos uma MainTable
    assert body["code_snapshots"] is not None
    assert lock_holder_pid(conn) is None


def test_process_saves_the_classroom_and_reports_trainability(api_client):
    client, conn = api_client
    upload = _upload(client).json()

    response = client.post(
        "/classroom-imports/process",
        json={
            "classroom_name": "Turma X",
            "raw_dir": upload["raw_dir"],
            "main_table": upload["main_tables"][0],
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["has_fatal"] is False
    assert body["per_assignment"] == [{"progsnap_assignment_id": 439, "trainable": True}]
    assert conn.execute("SELECT COUNT(*) FROM classroom;").fetchone()[0] == 1
    status = conn.execute("SELECT status FROM assignment;").fetchone()["status"]
    assert status == "ready_for_kc_generation"
    assert lock_holder_pid(conn) is None  # a trava foi liberada ao terminar


def test_process_refuses_paths_outside_the_data_root_before_reading(api_client):
    client, _ = api_client
    calls = []

    class _SpyUseCase:
        def execute(self, dto):
            calls.append(dto)

    client.app.dependency_overrides[import_classroom_dataset_use_case] = lambda: _SpyUseCase()
    raw_dir = str(settings.DATA_ROOT / "raw")
    try:
        for body in (
            # main_table em /etc/passwd, leitura arbitrária de arquivo se não fosse confinado.
            {"classroom_name": "X", "raw_dir": raw_dir, "main_table": "/etc/passwd"},
            {"classroom_name": "X", "raw_dir": "/etc", "main_table": f"{raw_dir}/MainTable.csv"},
            # `..` que normaliza para fora da raiz; a guarda resolve antes de conferir.
            {"classroom_name": "X", "raw_dir": raw_dir, "main_table": f"{raw_dir}/../../etc/passwd"},
        ):
            response = client.post("/classroom-imports/process", json=body)
            assert response.status_code == 400
    finally:
        client.app.dependency_overrides.clear()

    assert calls == []  # recusado antes, o use case nunca foi chamado


def test_an_upload_over_the_size_limit_is_refused_with_413(api_client, monkeypatch):
    client, _ = api_client
    # Um teto minúsculo exercita o guarda de streaming sem subir 512 MiB.
    monkeypatch.setattr(classroom_import_controller, "MAX_UPLOAD_BYTES", 16)

    assert _upload(client).status_code == 413
