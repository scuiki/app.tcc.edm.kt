"""Shared pytest fixtures for the edmkt_core suite.

The `a439_mini` fixture is a SYNTHETIC, hermetic ProgSnap2-shaped DataFrame (D-11/D-12):
it is generated in code, never loaded from the real CSEDM, and no test asserts a specific
AUC against it. The real-data fidelity check lives in the golden-run (plan 06, marked
`golden`, gated on EDMKT_CSEDM_PATH).
"""

from __future__ import annotations

import pandas as pd
import pytest
import torch

ASSIGNMENT_ID = 439

# Minimal compilable Java member declarations — javalang.parse_member_declaration
# parses these and extract_paths_javalang yields >= 1 AST path.
_JAVA_OK_A = "public int f(int x) { return x + 1; }"
_JAVA_OK_B = "public int g(int a, int b) { int s = a + b; return s; }"
_JAVA_OK_C = "public boolean h(int n) { if (n > 0) { return true; } return false; }"
# Deliberately malformed Java — exercises the try/except DoS guard (returns []).
_JAVA_BAD = "public int oops( { return ;;; }"


def _row(subject, problem, ts, event, score, code, csid):
    """One ProgSnap2 event row. `correct` follows the Code-DKT label rule:
    Run.Program with Score == 1.0 (Compile.Error never counts as correct)."""
    correct = int(event == "Run.Program" and score == 1.0)
    return {
        "SubjectID": subject,
        "ProblemID": problem,
        "AssignmentID": ASSIGNMENT_ID,
        "ServerTimestamp": ts,
        "EventType": event,
        "Score": score,
        "CodeStateID": csid,
        "Code": code,
        "correct": correct,
    }


@pytest.fixture
def a439_mini() -> pd.DataFrame:
    """Synthetic A439 ProgSnap2 subset.

    Guarantees:
      - 3 students across 3 problems (1, 2, 3).
      - EventType in {Run.Program, Compile.Error}; Score in {0.0, 1.0}.
      - Monotonic ServerTimestamp within each student.
      - Student "S_long" has > max_len(=5 in tests) events so truncation is exercised.
      - Problem 1 is repeated for every student, so is_first_attempt carries both
        True (first occurrence) and False (later occurrence) rows.
      - At least one malformed-Java snapshot to characterize the parser guard.
    """
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []

    def ts(student_offset, step):
        # distinct, monotonic-per-student timestamps
        return base + pd.Timedelta(hours=student_offset) + pd.Timedelta(minutes=step)

    # Student S1: problem 1 attempted twice (first fail, then pass) -> repeated problem.
    rows += [
        _row("S1", 1, ts(0, 0), "Run.Program", 0.0, _JAVA_OK_A, "c1"),
        _row("S1", 1, ts(0, 1), "Run.Program", 1.0, _JAVA_OK_A, "c2"),
        _row("S1", 2, ts(0, 2), "Run.Program", 1.0, _JAVA_OK_B, "c3"),
    ]

    # Student S2: a Compile.Error (malformed Java) then a passing run on problem 1,
    # plus problem 3 — repeated problem 1 again across the cohort.
    rows += [
        _row("S2", 1, ts(1, 0), "Compile.Error", 0.0, _JAVA_BAD, "c4"),
        _row("S2", 1, ts(1, 1), "Run.Program", 1.0, _JAVA_OK_A, "c5"),
        _row("S2", 3, ts(1, 2), "Run.Program", 0.0, _JAVA_OK_C, "c6"),
    ]

    # Student S_long: 8 events on problems 1/2/3 (> max_len=5) so truncation triggers,
    # with problem repetitions both inside and across the truncation window.
    long_plan = [
        (1, "Run.Program", 0.0, _JAVA_OK_A, "l1"),
        (2, "Run.Program", 0.0, _JAVA_OK_B, "l2"),
        (1, "Run.Program", 1.0, _JAVA_OK_A, "l3"),
        (3, "Run.Program", 0.0, _JAVA_OK_C, "l4"),
        (2, "Run.Program", 1.0, _JAVA_OK_B, "l5"),
        (3, "Run.Program", 1.0, _JAVA_OK_C, "l6"),
        (1, "Run.Program", 1.0, _JAVA_OK_A, "l7"),
        (2, "Run.Program", 1.0, _JAVA_OK_B, "l8"),
    ]
    for step, (pid, event, score, code, csid) in enumerate(long_plan):
        rows.append(_row("S_long", pid, ts(2, step), event, score, code, csid))

    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")
    return df


@pytest.fixture
def cpu_device() -> torch.device:
    """Force CPU so unit/characterization tests never touch the GPU (D-02)."""
    return torch.device("cpu")
