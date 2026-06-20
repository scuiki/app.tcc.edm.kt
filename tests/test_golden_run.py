"""Golden-run fidelity regression — A439 first-attempt AUC ±3pp (CORE-02, DEMO-01).

This is the phase's defining deliverable (CORE-02 ≡ DEMO-01): retrain Code-DKT on the
REAL CSEDM Spring 2019 data for AssignmentID 439 and assert the first-attempt AUC lands
in the ±3pp band [0.7027, 0.7627] anchored on the TCC 1 reference 73.2654%
(results/comparison_summary.json, Code-DKT A439 first_mean — D-08). The guard FAILS LOUD
outside the band: any future dependency bump, seed change, or operation reorder that
moves A439 out of band turns this test red (T-01-08).

Gating (D-07 fast-by-default):
  - Marked `@pytest.mark.golden`; the suite's default addopts (`-m 'not golden'`) deselect it.
  - The csedm_main_table fixture skips with a clear reason when EDMKT_CSEDM_PATH is unset,
    so the golden-run never runs (and never fails) on a machine without the dataset (D-12:
    the CSEDM is never copied into the repo).

The heavier on-demand check (multi-seed 42–51 / all 5 assignments) is NOT here by design
(D-07); this is the single-train gate run before milestones on the nitro GPU.
"""

from __future__ import annotations

import pytest

from edmkt_core import FROZEN_CONFIG, set_global_seed, train_and_evaluate
from edmkt_core.pipeline import split_by_subject

# Reference partition + anchor (Pitfall 3 / D-08).
A439 = 439
GOLDEN_LO = 0.7027  # 73.2654% - 3pp
GOLDEN_HI = 0.7627  # 73.2654% + 3pp


def assert_in_band(first_auc: float, lo: float = GOLDEN_LO, hi: float = GOLDEN_HI) -> None:
    """Raise a loud AssertionError naming the observed value and the band (CORE-02 #2).

    The guard must fail loud, not silently: a drift outside ±3pp of the TCC 1 reference
    is a reproducibility regression, and the message has to make the observed vs expected
    immediately legible in CI output.
    """
    if not (lo <= first_auc <= hi):
        raise AssertionError(
            f"first-attempt AUC {first_auc:.4f} is OUTSIDE the golden band "
            f"[{lo:.4f}, {hi:.4f}] (anchor 73.2654% ±3pp). Reproducibility drift: "
            f"a dependency, seed, or operation-order change moved A439 out of band."
        )


def test_band_fails_loud() -> None:
    """The band guard raises loud out of range and passes in range (CORE-02 #2).

    Pure unit test — no dataset needed, so it runs in the default fast suite.
    """
    assert_in_band(0.7300)  # in band: no raise
    assert_in_band(GOLDEN_LO)  # boundary inclusive
    assert_in_band(GOLDEN_HI)  # boundary inclusive

    for bad in (0.50, 0.90):
        with pytest.raises(AssertionError, match=r"OUTSIDE the golden band"):
            assert_in_band(bad)


def test_golden_run_skipped_without_path(monkeypatch) -> None:
    """With EDMKT_CSEDM_PATH unset the csedm fixture skips with a clear reason (D-07).

    Proves the fast-by-default gate: no dataset configured => the golden-run deselects
    itself rather than erroring. Runs in the default suite (no `golden` marker needed to
    observe the skip mechanism, which is the env gate, not the marker).
    """
    monkeypatch.delenv("EDMKT_CSEDM_PATH", raising=False)
    from tests.conftest import _resolve_csedm_path

    with pytest.raises(pytest.skip.Exception):
        _resolve_csedm_path()


@pytest.mark.golden
def test_golden_run_a439(csedm_main_table) -> None:
    """Retrain A439 on real CSEDM; first-attempt AUC must land in [0.7027, 0.7627].

    Reproduces the TCC 1 reference partition exactly (split_by_subject at random_state=1,
    min_attempts=3 — Pitfall 3), seeds non-strict on the GPU path (D-09/D-10, trusts the
    band), runs the public train_and_evaluate seam (plan 05), and asserts the band via the
    loud guard. FAILS LOUD outside the band (CORE-02 / DEMO-01).
    """
    train_df, test_df = split_by_subject(
        csedm_main_table, test_size=0.2, random_state=1, min_attempts=3
    )

    # D-10: non-strict on GPU; trusts the ±3pp band rather than paying bit-determinism cost.
    set_global_seed(FROZEN_CONFIG["seed"], strict=False)

    result = train_and_evaluate(
        train_df, FROZEN_CONFIG, test_df, assignment_id=A439
    )

    first_auc = result["first_auc"]
    print(f"\n[golden] A439 first-attempt AUC = {first_auc:.4f} "
          f"(band [{GOLDEN_LO:.4f}, {GOLDEN_HI:.4f}], anchor 73.2654%)")
    assert_in_band(first_auc)
