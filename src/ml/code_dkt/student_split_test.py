# Divisão por aluno + vocabulário só do treino, evita vazamento do teste no vocabulário de paths.

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import train_test_split

from ml.code_dkt import student_split
from ml.code_dkt.ast_paths import UNKNOWN_INDEX, extract_ast_paths
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


def _row(
    subject, problem, ts, score, code, snapshot_id, *, event="Run.Program", assignment=ASSIGNMENT_ID
):
    return {
        "student_id": subject,
        "problem_id": problem,
        "progsnap_assignment_id": assignment,
        "submitted_at": ts,
        "event_type": event,
        "score": score,
        "code_snapshot_id": snapshot_id,
        "code": code,
        "is_correct": int(event == "Run.Program" and score == 1.0),
    }


def _frame(rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")
    return df


def _split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    return student_split.split_students_into_train_and_test(
        df, progsnap_assignment_id=ASSIGNMENT_ID
    )


@pytest.fixture
def split_df() -> pd.DataFrame:
    # Subconjunto ProgSnap2 sintético, 6 alunos com 3 Run.Program e 1 com só 2 tentativas.
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []

    def ts(student_offset, step):
        return base + pd.Timedelta(hours=student_offset) + pd.Timedelta(minutes=step)

    # Seis alunos, cada um com um 3º snippet próprio (paths AST únicos).
    for i in range(6):
        sid = f"S{i}"
        rows += [
            _row(sid, 1, ts(i, 0), 0.0, _JAVA_OK_A, f"{sid}_c0"),
            _row(sid, 1, ts(i, 1), 1.0, _JAVA_OK_A, f"{sid}_c1"),
            _row(sid, 2, ts(i, 2), 1.0, _JAVA_PER_STUDENT[i], f"{sid}_c2"),
        ]

    # Aluno com só 2 tentativas, que entra na partição como os outros.
    rows += [
        _row("S_few", 1, ts(6, 0), 0.0, _JAVA_OK_A, "few_c0"),
        _row("S_few", 1, ts(6, 1), 1.0, _JAVA_OK_A, "few_c1"),
    ]
    return _frame(rows)


def test_split_by_subject_random_state_1(split_df):
    train_df, test_df = _split(split_df)

    train_students = set(train_df["student_id"])
    test_students = set(test_df["student_id"])

    # Disjunto por aluno, nenhum SubjectID vaza entre as partições.
    assert train_students.isdisjoint(test_students)
    assert train_students and test_students

    # Sem filtro de tentativas, o aluno de 2 tentativas está numa das partições.
    assert "S_few" in train_students | test_students

    # Determinístico, rodar de novo com o mesmo random_state reproduz a partição.
    train_df2, test_df2 = _split(split_df)
    assert set(train_df2["student_id"]) == train_students
    assert set(test_df2["student_id"]) == test_students

    # O random_state padrão é 1, NÃO 42.
    sig = inspect.signature(student_split.split_students_into_train_and_test)
    assert sig.parameters["random_state"].default == 1


def test_students_come_from_program_runs_in_row_order():
    # O Compile.Error de B vem antes de todo Run.Program, e só os Run.Program dão a ordem
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    order = ["S2", "A", "S0", "B", "S3", "S1"]
    rows = [_row("B", 1, base, 0.0, _JAVA_OK_A, "B_ce", event="Compile.Error")]
    rows += [
        _row(sid, 1, base + pd.Timedelta(minutes=i + 1), 1.0, _JAVA_OK_A, f"{sid}_c0")
        for i, sid in enumerate(order)
    ]
    df = _frame(rows)

    _, expected_test = train_test_split(
        np.array(order, dtype=object), test_size=0.2, random_state=1
    )
    # A ordem de todas as linhas poria B na frente, e com 6 alunos isso troca quem vai para o teste
    _, row_order_test = train_test_split(
        pd.unique(df["student_id"]), test_size=0.2, random_state=1
    )
    assert set(expected_test) != set(row_order_test)
    # A ordem alfabética também mudaria o teste, então só a ordem das linhas passa
    _, sorted_test = train_test_split(
        np.array(sorted(order), dtype=object), test_size=0.2, random_state=1
    )
    assert set(expected_test) != set(sorted_test)

    _, test_df = _split(df)
    assert set(test_df["student_id"]) == set(expected_test)


def test_every_student_with_a_program_run_in_the_assignment_enters_the_split():
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = [
        _row(f"S{i}", 1, base + pd.Timedelta(minutes=i), 0.0, _JAVA_OK_A, f"S{i}_c0")
        for i in range(5)
    ]
    # Uma execução só já basta, sem piso de tentativas
    rows.append(_row("ONE", 2, base + pd.Timedelta(hours=1), 1.0, _JAVA_OK_A, "one_c0"))
    # Só Compile.Error no exercício, como no repositório, fica fora
    rows.append(_row("CE", 1, base, 0.0, _JAVA_OK_A, "ce_c0", event="Compile.Error"))
    # Run.Program só em outro exercício também fica fora, e as linhas dele não voltam
    rows.append(_row("OTHER", 1, base, 1.0, _JAVA_OK_A, "other_c0", assignment=492))
    rows.append(_row("S0", 1, base, 1.0, _JAVA_OK_A, "s0_492", assignment=492))
    df = _frame(rows)

    train_df, test_df = _split(df)
    train_students, test_students = set(train_df["student_id"]), set(test_df["student_id"])

    assert train_students.isdisjoint(test_students)
    assert train_students | test_students == {"S0", "S1", "S2", "S3", "S4", "ONE"}
    both = pd.concat([train_df, test_df])
    assert set(both["progsnap_assignment_id"]) == {ASSIGNMENT_ID}
    assert "s0_492" not in set(both["code_snapshot_id"])


def test_vocab_train_only(split_df):
    train_df, test_df = _split(split_df)

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
    train_df, test_df = _split(split_df)

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
    # Coluna do path (idx 1) mapeia o inédito para o UNKNOWN_INDEX; pelo menos um path é inédito.
    n_paths = min(len(held_out_paths), 50)
    oov_count = int(np.sum(arr[:n_paths, 1] == UNKNOWN_INDEX))
    assert oov_count > 0
