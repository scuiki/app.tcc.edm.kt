# Divisão por aluno + vocabulário só do treino, evita vazamento do teste no vocabulário de paths.

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from ml.code_dkt import student_split
from ml.code_dkt.ast_paths import extract_ast_paths
from ml.code_dkt.model_input import ast_paths_to_index_array

ASSIGNMENT_ID = 439

_JAVA_OK_A = "public int f(int x) { return x + 1; }"
# Seis corpos de método distintos, um por aluno, garantem paths OOV no teste por construção.
_JAVA_PER_STUDENT = [
    "public int g0(int a, int b) { int s = a + b; return s; }",
    "public int g1(int a) { for (int i = 0; i < a; i++) { a = a * 2; } return a; }",
    "public boolean g2(int n) { if (n > 0) { return true; } return false; }",
    "public int g3(int n) { while (n > 0) { n = n - 1; } return n; }",
    "public int g4(int[] xs) { int t = 0; for (int x : xs) { t += x; } return t; }",
    "public String g5(boolean b) { return b ? \"yes\" : \"no\"; }",
]
# Snippet reservado, estrutura try/catch ausente de todos os corpos dos alunos.
_JAVA_OK_C = "public int h(int n) { try { return 10 / n; } catch (Exception e) { return -1; } }"


def _row(subject, problem, ts, score, code, snapshot_id):
    return {
        "student_id": subject,
        "problem_id": problem,
        "progsnap_assignment_id": ASSIGNMENT_ID,
        "submitted_at": ts,
        "event_type": "Run.Program",
        "score": score,
        "code_snapshot_id": snapshot_id,
        "code": code,
        "is_correct": int(score == 1.0),
    }


@pytest.fixture
def split_df() -> pd.DataFrame:
    # Subconjunto ProgSnap2 sintético, 6 alunos elegíveis (>=3 Run.Program) + 1 com só 2 tentativas.
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []

    def ts(student_offset, step):
        return base + pd.Timedelta(hours=student_offset) + pd.Timedelta(minutes=step)

    # Seis alunos elegíveis, cada um com um 3º snippet próprio (paths AST únicos).
    for i in range(6):
        sid = f"S{i}"
        rows += [
            _row(sid, 1, ts(i, 0), 0.0, _JAVA_OK_A, f"{sid}_c0"),
            _row(sid, 1, ts(i, 1), 1.0, _JAVA_OK_A, f"{sid}_c1"),
            _row(sid, 2, ts(i, 2), 1.0, _JAVA_PER_STUDENT[i], f"{sid}_c2"),
        ]

    # Aluno inelegível, só 2 tentativas, cai fora por min_attempts=3.
    rows += [
        _row("S_few", 1, ts(6, 0), 0.0, _JAVA_OK_A, "few_c0"),
        _row("S_few", 1, ts(6, 1), 1.0, _JAVA_OK_A, "few_c1"),
    ]

    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    return df


def test_split_by_subject_random_state_1(split_df):
    train_df, test_df = student_split.split_students_into_train_and_test(split_df)

    train_students = set(train_df["student_id"])
    test_students = set(test_df["student_id"])

    # Disjunto por aluno, nenhum SubjectID vaza entre as partições.
    assert train_students.isdisjoint(test_students)
    assert train_students and test_students

    # Filtro de min_attempts aplicado, o aluno de 2 tentativas não está em nenhuma partição.
    assert "S_few" not in train_students
    assert "S_few" not in test_students

    # Determinístico, rodar de novo com o mesmo random_state reproduz a partição.
    train_df2, test_df2 = student_split.split_students_into_train_and_test(split_df)
    assert set(train_df2["student_id"]) == train_students
    assert set(test_df2["student_id"]) == test_students

    # O random_state padrão é 1, NÃO 42.
    sig = inspect.signature(student_split.split_students_into_train_and_test)
    assert sig.parameters["random_state"].default == 1


def test_vocab_train_only(split_df):
    train_df, test_df = student_split.split_students_into_train_and_test(split_df)

    code_states = dict(
        zip(split_df["code_snapshot_id"].astype(str), split_df["code"])
    )
    ast_paths_by_snapshot = {
        snapshot_id: extract_ast_paths(code) for snapshot_id, code in code_states.items()
    }

    train_snapshot_ids = set(train_df["code_snapshot_id"].astype(str))
    test_snapshot_ids = set(test_df["code_snapshot_id"].astype(str))

    # Contrato pela assinatura, o helper de vocabulário recebe só o cache/ids do treino.
    token_to_idx, path_to_idx = student_split.build_train_only_vocabulary(ast_paths_by_snapshot, train_snapshot_ids)

    # Um path só do teste (de um code state presente só lá) precisa estar ausente.
    test_only_snapshot_ids = test_snapshot_ids - train_snapshot_ids
    test_only_paths = {
        p[1]
        for c in test_only_snapshot_ids
        for p in ast_paths_by_snapshot.get(c, [])
    }
    train_paths = {
        p[1]
        for c in train_snapshot_ids
        for p in ast_paths_by_snapshot.get(c, [])
    }
    unseen = test_only_paths - train_paths
    assert unseen, "fixture must contain at least one test-only path"
    for path_str in unseen:
        assert path_str not in path_to_idx


def test_oov_positive(split_df):
    train_df, test_df = student_split.split_students_into_train_and_test(split_df)

    code_states = dict(
        zip(split_df["code_snapshot_id"].astype(str), split_df["code"])
    )
    ast_paths_by_snapshot = {
        snapshot_id: extract_ast_paths(code) for snapshot_id, code in code_states.items()
    }
    train_snapshot_ids = set(train_df["code_snapshot_id"].astype(str))
    token_to_idx, path_to_idx = student_split.build_train_only_vocabulary(ast_paths_by_snapshot, train_snapshot_ids)

    # Snippet reservado com estrutura ausente do treino (while) vira paths OOV.
    held_out_paths = extract_ast_paths(_JAVA_OK_C)
    assert held_out_paths, "held-out snippet must yield >= 1 path"

    arr = ast_paths_to_index_array(held_out_paths, token_to_idx, path_to_idx, R=50)
    # Coluna do path (idx 1) mapeia OOV para 0; pelo menos um path reservado é inédito.
    n_paths = min(len(held_out_paths), 50)
    oov_count = int(np.sum(arr[:n_paths, 1] == 0))
    assert oov_count > 0
