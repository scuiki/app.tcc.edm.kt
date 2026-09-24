"""Split-before-vocab contract + OOV>0 held-out tests (CORE-04, T-01-05).

The threat is test-set leakage into the path vocabulary: building vocab over the
train+test union drives OOV->0 and inflates AUC (RESEARCH Anti-Patterns). These
tests pin the discipline that lives in notebook 06 cell 14:
  - split_by_subject partitions students disjointly at random_state=1 (Pitfall 3, NOT 42);
  - the vocab helper only ever sees the train partition's CodeStateIDs;
  - a held-out tensorization against the train-only vocab yields path-OOV > 0.

No real CSEDM, no AUC assertions — the numerics oracle is the regression test (plan 06).
"""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from edmkt_core import pipeline
from edmkt_core.features import extract_paths_javalang, paths_to_tensor

ASSIGNMENT_ID = 439

_JAVA_OK_A = "public int f(int x) { return x + 1; }"
# Six structurally distinct method bodies — one per student — so each student
# contributes AST paths unique to itself. Whatever the random partition, the test
# students' snippets yield paths unseen in train (OOV > 0 by construction, not by
# coupling the test to which SubjectIDs land where).
_JAVA_PER_STUDENT = [
    "public int g0(int a, int b) { int s = a + b; return s; }",
    "public int g1(int a) { for (int i = 0; i < a; i++) { a = a * 2; } return a; }",
    "public boolean g2(int n) { if (n > 0) { return true; } return false; }",
    "public int g3(int n) { while (n > 0) { n = n - 1; } return n; }",
    "public int g4(int[] xs) { int t = 0; for (int x : xs) { t += x; } return t; }",
    "public String g5(boolean b) { return b ? \"yes\" : \"no\"; }",
]
# Held-out snippet whose structure (try/catch) is absent from every student body.
_JAVA_OK_C = "public int h(int n) { try { return 10 / n; } catch (Exception e) { return -1; } }"


def _row(subject, problem, ts, score, code, csid):
    return {
        "student_id": subject,
        "problem_id": problem,
        "progsnap_assignment_id": ASSIGNMENT_ID,
        "submitted_at": ts,
        "event_type": "Run.Program",
        "score": score,
        "code_snapshot_id": csid,
        "code": code,
        "is_correct": int(score == 1.0),
    }


@pytest.fixture
def split_df() -> pd.DataFrame:
    """Synthetic ProgSnap2 subset for the split/vocab contract.

    Six eligible students (>= 3 Run.Program attempts each) plus one ineligible
    student with 2 attempts, so min_attempts filtering is observable. Each student
    owns a structurally distinct snippet, so the held-out (test) partition always
    contributes a path unseen in train (OOV > 0), independent of the partition draw.
    """
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []

    def ts(student_offset, step):
        return base + pd.Timedelta(hours=student_offset) + pd.Timedelta(minutes=step)

    # Six eligible students, each with a unique third snippet (its own AST paths).
    for i in range(6):
        sid = f"S{i}"
        rows += [
            _row(sid, 1, ts(i, 0), 0.0, _JAVA_OK_A, f"{sid}_c0"),
            _row(sid, 1, ts(i, 1), 1.0, _JAVA_OK_A, f"{sid}_c1"),
            _row(sid, 2, ts(i, 2), 1.0, _JAVA_PER_STUDENT[i], f"{sid}_c2"),
        ]

    # Ineligible student: only 2 attempts -> dropped by min_attempts=3.
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
    train_df, test_df = pipeline.split_by_subject(split_df)

    train_students = set(train_df["student_id"])
    test_students = set(test_df["student_id"])

    # Disjoint by student: no SubjectID leaks across the partition boundary.
    assert train_students.isdisjoint(test_students)
    assert train_students and test_students

    # min_attempts filtering applied: the 2-attempt student is in neither partition.
    assert "S_few" not in train_students
    assert "S_few" not in test_students

    # Deterministic: re-running with the same random_state reproduces the partition.
    train_df2, test_df2 = pipeline.split_by_subject(split_df)
    assert set(train_df2["student_id"]) == train_students
    assert set(test_df2["student_id"]) == test_students

    # Default random_state is 1, NOT 42 (Pitfall 3).
    sig = inspect.signature(pipeline.split_by_subject)
    assert sig.parameters["random_state"].default == 1


def test_vocab_train_only(split_df):
    train_df, test_df = pipeline.split_by_subject(split_df)

    code_states = dict(
        zip(split_df["code_snapshot_id"].astype(str), split_df["code"])
    )
    cache_raw = {
        csid: extract_paths_javalang(code) for csid, code in code_states.items()
    }

    train_csids = set(train_df["code_snapshot_id"].astype(str))
    test_csids = set(test_df["code_snapshot_id"].astype(str))

    # Contract by signature: the vocab helper takes only the train cache/csids.
    token_to_idx, path_to_idx = pipeline.build_train_vocab(cache_raw, train_csids)

    # A test-only path (from a code state present only in test) must be absent.
    test_only_csids = test_csids - train_csids
    test_only_paths = {
        p[1]
        for c in test_only_csids
        for p in cache_raw.get(c, [])
    }
    train_paths = {
        p[1]
        for c in train_csids
        for p in cache_raw.get(c, [])
    }
    unseen = test_only_paths - train_paths
    assert unseen, "fixture must contain at least one test-only path"
    for path_str in unseen:
        assert path_str not in path_to_idx


def test_oov_positive(split_df):
    train_df, test_df = pipeline.split_by_subject(split_df)

    code_states = dict(
        zip(split_df["code_snapshot_id"].astype(str), split_df["code"])
    )
    cache_raw = {
        csid: extract_paths_javalang(code) for csid, code in code_states.items()
    }
    train_csids = set(train_df["code_snapshot_id"].astype(str))
    token_to_idx, path_to_idx = pipeline.build_train_vocab(cache_raw, train_csids)

    # Held-out snippet with structure unseen in train (while-loop) -> OOV paths.
    held_out_paths = extract_paths_javalang(_JAVA_OK_C)
    assert held_out_paths, "held-out snippet must yield >= 1 path"

    arr = paths_to_tensor(held_out_paths, token_to_idx, path_to_idx, R=50)
    # path column (idx 1) maps OOV -> 0; at least one held-out path is unseen.
    n_paths = min(len(held_out_paths), 50)
    oov_count = int(np.sum(arr[:n_paths, 1] == 0))
    assert oov_count > 0
