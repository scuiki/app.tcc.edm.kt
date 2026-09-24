"""Regression test against the TCC 1 reference run — A439 first-attempt AUC ±3pp (CORE-02, DEMO-01).

This is the phase's defining deliverable (CORE-02 ≡ DEMO-01): retrain Code-DKT on the
REAL CSEDM Spring 2019 data for AssignmentID 439 and assert the first-attempt AUC lands
within TOLERANCE_PP of REFERENCE_AUC, the TCC 1 reference run (73.2654%, from
results/comparison_summary.json, Code-DKT A439 first_mean — D-08). The guard FAILS LOUD
outside the band: any future dependency bump, seed change, or operation reorder that
moves A439 out of band turns this test red (T-01-08).

What it protects is the PROCEDURE (architecture, hyperparameters, operation order, seed,
pinned dependencies) — not any set of trained weights. It should run whenever ml or
its dependencies change; the models teachers train in the app are only reported (uncertainty
frame), never tested against a reference.

Gating (D-07 fast-by-default):
  - Marked `@pytest.mark.regression`; the suite's default addopts (`-m 'not regression'`)
    deselect it.
  - The csedm_main_table fixture skips with a clear reason when EDMKT_CSEDM_PATH is unset,
    so the regression test never runs (and never fails) on a machine without the dataset
    (D-12: the CSEDM is never copied into the repo).

The heavier on-demand check (multi-seed 42–51 / all 5 assignments) is NOT here by design
(D-07); this is the single-train gate run before milestones on the nitro GPU.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import pytest

from ml.code_dkt.train_and_evaluate import train_and_evaluate
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS
from ml.reproducibility.random_seed import seed_all_random_generators
from ml.code_dkt.student_split import split_students_into_train_and_test


def _resolve_csedm_path() -> Path:
    """Resolve EDMKT_CSEDM_PATH or skip the regression test with a clear reason (D-07/D-12).

    The real CSEDM is NEVER copied into the repo and NEVER read from ../tcc.edm.kt/data
    (D-12); the operator points EDMKT_CSEDM_PATH at the provisioned dataset on nitro. When
    it is unset (or the dir/MainTable is missing) the regression test skips cleanly rather than
    erroring, so the default fast suite stays green on machines without the dataset.
    """
    raw = os.environ.get("EDMKT_CSEDM_PATH")
    if not raw:
        pytest.skip(
            "EDMKT_CSEDM_PATH unset — regression test skipped (D-07 fast-by-default). "
            "Set it to the provisioned CSEDM dir (with MainTable.csv + CodeStates/) to run."
        )
    data_dir = Path(raw)
    if not (data_dir / "MainTable.csv").exists():
        pytest.skip(f"EDMKT_CSEDM_PATH={data_dir} has no MainTable.csv — regression test skipped.")
    return data_dir

# Minimal compilable Java member declarations — javalang.parse_member_declaration
# parses these and extract_ast_paths yields >= 1 AST path.
_JAVA_OK_A = "public int f(int x) { return x + 1; }"
_JAVA_OK_B = "public int g(int a, int b) { int s = a + b; return s; }"
_JAVA_OK_C = "public boolean h(int n) { if (n > 0) { return true; } return false; }"
# Deliberately malformed Java — exercises the try/except DoS guard (returns []).
_JAVA_BAD = "public int oops( { return ;;; }"
# Parses (parse_member_declaration accepts it) but has no leaf pairs, so
# extract_ast_paths returns [] WITHOUT raising — the parsed_sem_paths case
# that the 3-way classifier must separate from parse_failed (D-09).
_JAVA_EMPTY_CLASS = "class C {}"


@pytest.fixture
def csedm_main_table() -> pd.DataFrame:
    """Real CSEDM Spring 2019 events, shaped for the public train_and_evaluate seam.

    Reads EDMKT_CSEDM_PATH (skip-if-unset, D-07/D-12) and reproduces the TCC 1 Code-DKT
    input exactly: Run.Program events only (the BKT/DKT filter the Code-DKT regression test
    consumed — sequences_bkt_dkt.pkl, notebook 06 cell 4 asserts EventType == Run.Program),
    correct = (Score == 1.0), the per-row Java snapshot joined from CodeStates.csv on
    CodeStateID, and types normalized like data_loader.load_spring2019_split
    (ServerTimestamp -> UTC datetime, AssignmentID/ProblemID -> Int64).

    split_students_into_train_and_test(random_state=1, min_attempts=3) then reproduces the reference
    partition (Pitfall 3); the Code column flows into code_by_snapshot_id and `correct`
    into build_model_input_tensors/predict.
    """
    data_dir = _resolve_csedm_path()

    df = pd.read_csv(data_dir / "MainTable.csv")
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True, errors="coerce")
    df["AssignmentID"] = pd.to_numeric(df["AssignmentID"], errors="coerce").astype("Int64")
    df["ProblemID"] = pd.to_numeric(df["ProblemID"], errors="coerce").astype("Int64")

    # Run.Program only + binary label (data_loader.filter_for_bkt_dkt — the exact filter
    # behind sequences_bkt_dkt.pkl that the TCC 1 Code-DKT run trained on).
    df = df[df["EventType"] == "Run.Program"].copy()
    df["correct"] = (df["Score"] == 1.0).astype(int)

    # Join the Java snapshot per event (CodeStateID -> Code) so the pure-DataFrame seam
    # (code_by_snapshot_id) sees inline code without reading a CSEDM path itself (CORE-01).
    code_states = pd.read_csv(data_dir / "CodeStates" / "CodeStates.csv")
    code_map = dict(zip(code_states["CodeStateID"].astype(str), code_states["Code"].fillna("")))
    df["Code"] = df["CodeStateID"].astype(str).map(code_map).fillna("")

    # Same translation the import applies (ingestion/clean): from here on, glossary names.
    from api.classroom_import.domain.submission_cleaning import PROGSNAP_TO_CLEANED_COLUMNS

    df = df.rename(columns={**PROGSNAP_TO_CLEANED_COLUMNS, "correct": "is_correct"})
    return df.reset_index(drop=True)

# Reference partition (Pitfall 3 / D-08).
A439 = 439

# TCC 1 reference run: Code-DKT A439 first-attempt AUC (results/comparison_summary.json).
REFERENCE_AUC = 0.732654
# Tolerance in absolute AUC (3pp): absorbs seed variance (std ≈ 1.34pp in TCC 1) and the gap
# between CODE_DKT_HYPERPARAMETERS (Shi et al. protocol, hidden_dim=128) and the TCC 1 grid best
# (hidden_dim=200) that produced the reference.
TOLERANCE_PP = 0.03

BAND_LO = round(REFERENCE_AUC - TOLERANCE_PP, 4)  # 0.7027
BAND_HI = round(REFERENCE_AUC + TOLERANCE_PP, 4)  # 0.7627


def assert_in_band(first_auc: float, lo: float = BAND_LO, hi: float = BAND_HI) -> None:
    """Raise a loud AssertionError naming the observed value and the band (CORE-02 #2).

    The guard must fail loud, not silently: a drift outside ±3pp of the TCC 1 reference run
    is a regression of the frozen procedure, and the message has to make the observed vs
    expected immediately legible in CI output.
    """
    if not (lo <= first_auc <= hi):
        raise AssertionError(
            f"first-attempt AUC {first_auc:.4f} is OUTSIDE the regression band "
            f"[{lo:.4f}, {hi:.4f}] (reference run {REFERENCE_AUC:.4%} ±3pp). "
            f"A dependency, seed, or operation-order change moved A439 out of band."
        )


def test_band_fails_loud() -> None:
    """The band guard raises loud out of range and passes in range (CORE-02 #2).

    Pure unit test — no dataset needed, so it runs in the default fast suite.
    """
    assert_in_band(0.7300)  # in band: no raise
    assert_in_band(BAND_LO)  # boundary inclusive
    assert_in_band(BAND_HI)  # boundary inclusive

    for bad in (0.50, 0.90):
        with pytest.raises(AssertionError, match=r"OUTSIDE the regression band"):
            assert_in_band(bad)


def test_band_derives_from_reference() -> None:
    """The band is REFERENCE_AUC ± TOLERANCE_PP — the two documented limits, not two magic numbers."""
    assert BAND_LO == 0.7027
    assert BAND_HI == 0.7627


def test_regression_skipped_without_path(monkeypatch) -> None:
    """With EDMKT_CSEDM_PATH unset the csedm fixture skips with a clear reason (D-07).

    Proves the fast-by-default gate: no dataset configured => the regression test deselects
    itself rather than erroring. Runs in the default suite (no `regression` marker needed to
    observe the skip mechanism, which is the env gate, not the marker).
    """
    monkeypatch.delenv("EDMKT_CSEDM_PATH", raising=False)
    with pytest.raises(pytest.skip.Exception):
        _resolve_csedm_path()


@pytest.mark.regression
def test_regression_a439(csedm_main_table) -> None:
    """Retrain A439 on real CSEDM; first-attempt AUC must land in [0.7027, 0.7627].

    Reproduces the TCC 1 reference partition exactly (split_students_into_train_and_test at random_state=1,
    min_attempts=3 — Pitfall 3), seeds non-strict on the GPU path (D-09/D-10, trusts the
    band), runs the public train_and_evaluate seam (plan 05), and asserts the band via the
    loud guard. FAILS LOUD outside the band (CORE-02 / DEMO-01).
    """
    train_df, test_df = split_students_into_train_and_test(
        csedm_main_table, test_size=0.2, random_state=1, min_attempts=3
    )

    # D-10: non-strict on GPU; trusts the ±3pp band rather than paying bit-determinism cost.
    seed_all_random_generators(CODE_DKT_HYPERPARAMETERS["seed"], strict=False)

    result = train_and_evaluate(
        train_df, CODE_DKT_HYPERPARAMETERS, test_df, progsnap_assignment_id=A439
    )

    first_auc = result["first_attempt_auc"]
    print(f"\n[regression] A439 first-attempt AUC = {first_auc:.4f} "
          f"(band [{BAND_LO:.4f}, {BAND_HI:.4f}], reference run {REFERENCE_AUC:.4%})")
    assert_in_band(first_auc)
