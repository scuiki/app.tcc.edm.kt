# a439_mini — synthetic hermetic fixture

This is a **synthetic** ProgSnap2-shaped subset built in code by the `a439_mini`
pytest fixture (`tests/conftest.py`). It is **not** the real CSEDM dataset and must
never be confused with it (D-11/D-12).

## What it is

A handful of fabricated students (`S1`, `S2`, `S_long`) attempting three problems
(`1`, `2`, `3`) under `AssignmentID == 439`, with:

- `EventType` in `{Run.Program, Compile.Error}`
- `Score` in `{0.0, 1.0}` (ground-truth `correct = Run.Program & Score == 1.0`)
- monotonic `ServerTimestamp` per student
- minimal compilable Java in `Code` (so `javalang` yields ≥ 1 AST path) plus one
  deliberately malformed snippet (to characterize the parser's `try/except` guard)
- at least one repeated problem (so `is_first_attempt` has both `True` and `False`)
- one over-`max_len` student (`S_long`, 8 events) so truncation is exercised

## What it is NOT

- It is **not** loaded from disk, pickled, or derived from the real CSEDM.
- **No test asserts a specific AUC** against this fixture. Numerics are arbitrary on
  synthetic data; the only real-data fidelity check is the **golden-run** (plan 06),
  which is marked `golden`, reads the CSEDM via `EDMKT_CSEDM_PATH`, and asserts A439
  first-attempt AUC ∈ [70.27, 76.27].

The characterization tests use this fixture only to pin **shapes and behavior**
(path extraction, vocab/tensor mapping, sequence build/truncate, metric separation,
training callback/device wiring) of the verbatim TCC 1 port before any correction.
