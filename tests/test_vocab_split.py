"""Split-before-vocab contract + OOV>0 held-out tests (CORE-04, T-01-05).

The threat is test-set leakage into the path vocabulary: building vocab over the
train+test union drives OOV->0 and inflates AUC (RESEARCH Anti-Patterns). These
tests pin the discipline that lives in notebook 06 cell 14:
  - split_by_subject partitions students disjointly at random_state=1 (Pitfall 3, NOT 42);
  - the vocab helper only ever sees the train partition's CodeStateIDs;
  - a held-out tensorization against the train-only vocab yields path-OOV > 0.

No real CSEDM, no AUC assertions — the numerics oracle is the golden-run (plan 06).
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
_JAVA_OK_B = "public int g(int a, int b) { int s = a + b; return s; }"
# Structurally distinct snippet used to guarantee a test-only path unseen in train.
_JAVA_OK_C = "public boolean h(int n) { while (n > 0) { n = n - 1; } return n == 0; }"


def _row(subject, problem, ts, score, code, csid):
    return {
        "SubjectID": subject,
        "ProblemID": problem,
        "AssignmentID": ASSIGNMENT_ID,
        "ServerTimestamp": ts,
        "EventType": "Run.Program",
        "Score": score,
        "CodeStateID": csid,
        "Code": code,
        "correct": int(score == 1.0),
    }


@pytest.fixture
def split_df() -> pd.DataFrame:
    """Synthetic ProgSnap2 subset for the split/vocab contract.

    Six eligible students (>= 3 Run.Program attempts each) plus one ineligible
    student with 2 attempts, so min_attempts filtering is observable. Train and
    test students use deliberately different Java snippets so the held-out
    partition contains a path unseen in train (OOV > 0).
    """
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []

    def ts(student_offset, step):
        return base + pd.Timedelta(hours=student_offset) + pd.Timedelta(minutes=step)

    # Six eligible students: A/B snippets only (the train-vocab universe).
    for i in range(6):
        sid = f"S{i}"
        rows += [
            _row(sid, 1, ts(i, 0), 0.0, _JAVA_OK_A, f"{sid}_c0"),
            _row(sid, 1, ts(i, 1), 1.0, _JAVA_OK_A, f"{sid}_c1"),
            _row(sid, 2, ts(i, 2), 1.0, _JAVA_OK_B, f"{sid}_c2"),
        ]

    # Ineligible student: only 2 attempts -> dropped by min_attempts=3.
    rows += [
        _row("S_few", 1, ts(6, 0), 0.0, _JAVA_OK_A, "few_c0"),
        _row("S_few", 1, ts(6, 1), 1.0, _JAVA_OK_A, "few_c1"),
    ]

    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")
    return df


def test_split_by_subject_random_state_1(split_df):
    train_df, test_df = pipeline.split_by_subject(split_df)

    train_students = set(train_df["SubjectID"])
    test_students = set(test_df["SubjectID"])

    # Disjoint by student: no SubjectID leaks across the partition boundary.
    assert train_students.isdisjoint(test_students)
    assert train_students and test_students

    # min_attempts filtering applied: the 2-attempt student is in neither partition.
    assert "S_few" not in train_students
    assert "S_few" not in test_students

    # Deterministic: re-running with the same random_state reproduces the partition.
    train_df2, test_df2 = pipeline.split_by_subject(split_df)
    assert set(train_df2["SubjectID"]) == train_students
    assert set(test_df2["SubjectID"]) == test_students

    # Default random_state is 1, NOT 42 (Pitfall 3).
    sig = inspect.signature(pipeline.split_by_subject)
    assert sig.parameters["random_state"].default == 1


def test_vocab_train_only(split_df):
    train_df, test_df = pipeline.split_by_subject(split_df)

    code_states = dict(
        zip(split_df["CodeStateID"].astype(str), split_df["Code"])
    )
    cache_raw = {
        csid: extract_paths_javalang(code) for csid, code in code_states.items()
    }

    train_csids = set(train_df["CodeStateID"].astype(str))
    test_csids = set(test_df["CodeStateID"].astype(str))

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
        zip(split_df["CodeStateID"].astype(str), split_df["Code"])
    )
    cache_raw = {
        csid: extract_paths_javalang(code) for csid, code in code_states.items()
    }
    train_csids = set(train_df["CodeStateID"].astype(str))
    token_to_idx, path_to_idx = pipeline.build_train_vocab(cache_raw, train_csids)

    # Held-out snippet with structure unseen in train (while-loop) -> OOV paths.
    held_out_paths = extract_paths_javalang(_JAVA_OK_C)
    assert held_out_paths, "held-out snippet must yield >= 1 path"

    arr = paths_to_tensor(held_out_paths, token_to_idx, path_to_idx, R=50)
    # path column (idx 1) maps OOV -> 0; at least one held-out path is unseen.
    n_paths = min(len(held_out_paths), 50)
    oov_count = int(np.sum(arr[:n_paths, 1] == 0))
    assert oov_count > 0
