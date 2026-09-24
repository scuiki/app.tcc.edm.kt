# Fixtures usadas por várias áreas. As de uma área só ficam em tests/fixtures/<área>.py.

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from tests.fixtures.sample_data import (
    JAVA_BAD,
    JAVA_OK_A,
    JAVA_OK_B,
    JAVA_OK_C,
    cleaned_row,
    with_cleaned_dtypes,
)

pytest_plugins = [
    "tests.fixtures.classroom_import",
    "tests.fixtures.knowledge_components",
    "tests.fixtures.model_training",
    "tests.fixtures.mastery_dashboard",
    "tests.fixtures.ml",
]


@pytest.fixture
def a439_mini() -> pd.DataFrame:
    # 3 alunos em 3 problemas, com repetição de problema, um Java quebrado e um aluno longo
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []

    def ts(student_offset, step):
        return base + pd.Timedelta(hours=student_offset) + pd.Timedelta(minutes=step)

    rows += [
        cleaned_row("S1", 1, ts(0, 0), "Run.Program", 0.0, JAVA_OK_A, "c1"),
        cleaned_row("S1", 1, ts(0, 1), "Run.Program", 1.0, JAVA_OK_A, "c2"),
        cleaned_row("S1", 2, ts(0, 2), "Run.Program", 1.0, JAVA_OK_B, "c3"),
    ]
    rows += [
        cleaned_row("S2", 1, ts(1, 0), "Compile.Error", 0.0, JAVA_BAD, "c4"),
        cleaned_row("S2", 1, ts(1, 1), "Run.Program", 1.0, JAVA_OK_A, "c5"),
        cleaned_row("S2", 3, ts(1, 2), "Run.Program", 0.0, JAVA_OK_C, "c6"),
    ]
    # 8 eventos, mais que o max_len=5 dos testes, para exercitar o truncamento
    long_plan = [
        (1, "Run.Program", 0.0, JAVA_OK_A, "l1"),
        (2, "Run.Program", 0.0, JAVA_OK_B, "l2"),
        (1, "Run.Program", 1.0, JAVA_OK_A, "l3"),
        (3, "Run.Program", 0.0, JAVA_OK_C, "l4"),
        (2, "Run.Program", 1.0, JAVA_OK_B, "l5"),
        (3, "Run.Program", 1.0, JAVA_OK_C, "l6"),
        (1, "Run.Program", 1.0, JAVA_OK_A, "l7"),
        (2, "Run.Program", 1.0, JAVA_OK_B, "l8"),
    ]
    for step, (pid, event, score, code, snapshot_id) in enumerate(long_plan):
        rows.append(cleaned_row("S_long", pid, ts(2, step), event, score, code, snapshot_id))

    return with_cleaned_dtypes(pd.DataFrame(rows))


@pytest.fixture
def data_root(tmp_path, monkeypatch) -> Path:
    # Tudo o que se grava em data/ vai para o tmp_path do teste
    from api.shared.infrastructure import settings

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    return tmp_path


@pytest.fixture
def tmp_db(tmp_path):
    from api.shared.infrastructure.database.migrations.runner import run_migrations
    from api.shared.infrastructure.database.sqlite_connection import connect

    conn = connect(str(tmp_path / "app.db"))
    run_migrations(conn)
    return conn


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    # Devolve (client, conn), e as duas conexões apontam para o mesmo app.db do tmp_path
    from fastapi.testclient import TestClient

    from api.main import create_app
    from api.shared.infrastructure import settings
    from api.shared.infrastructure.database.sqlite_connection import connect

    db_path = tmp_path / "app.db"
    monkeypatch.setenv("EDMKT_DB_PATH", str(db_path))
    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)

    with TestClient(create_app()) as client:
        conn = connect(str(db_path))
        try:
            yield client, conn
        finally:
            conn.close()
