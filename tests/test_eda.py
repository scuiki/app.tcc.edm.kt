"""Testes RED de EDA (DASH-04) — agregados do Parquet canônico, SEM modelo treinado.

Pinam o contrato de `edmkt_app.eda` antes de existir (Wave 0): taxa de acerto por assignment,
curva de aprendizado (média de `correct` por número de tentativa) e taxa de compile-error,
computados direto do Parquet canônico da Fase 3 (CANONICAL_COLUMNS de clean.py) — nenhum
artefato de modelo é tocado (D-06: EDA disponível antes de qualquer treino). Todos FALHAM
agora com ImportError em `edmkt_app.eda`.

O Parquet sintético é derivado do fixture a439_mini (synthetic/hermético, NUNCA o CSEDM real):
escrevemos as CANONICAL_COLUMNS num .parquet sob tmp_path e apontamos as funções de EDA p/ ele.
"""

from __future__ import annotations

import pandas as pd
import pytest


def _write_canonical_parquet(df: pd.DataFrame, path) -> None:
    # a439_mini já traz SubjectID/AssignmentID/ProblemID/CodeStateID/Code/Score/ServerTimestamp/
    # EventType/correct — exatamente as CANONICAL_COLUMNS que o clean emite (clean.py:26).
    from edmkt_app.ingestion.clean import CANONICAL_COLUMNS

    canonical = df[CANONICAL_COLUMNS].copy()
    canonical.to_parquet(path, index=False)


@pytest.fixture
def canonical_parquet(tmp_path, a439_mini):
    pq = tmp_path / "assignment_439.parquet"
    _write_canonical_parquet(a439_mini, pq)
    return pq


def test_success_rate_by_assignment_no_model(canonical_parquet):
    # DASH-04: taxa de acerto = média de `correct` sobre eventos Run.Program por AssignmentID.
    # NENHUM modelo é carregado — prova que o EDA roda sem treino (D-06).
    from edmkt_app.eda import success_rate_by_assignment

    rates = success_rate_by_assignment(canonical_parquet)

    # a439_mini é todo do AssignmentID 439; a taxa é uma fração em [0,1].
    assert 439 in rates
    assert 0.0 <= rates[439] <= 1.0
    # invariante de coerência: bate com a média de `correct` nos Run.Program do próprio fixture.
    df = pd.read_parquet(canonical_parquet)
    runs = df[df["EventType"] == "Run.Program"]
    assert rates[439] == pytest.approx(runs["correct"].mean())


def test_learning_curve_mean_correct_by_attempt(canonical_parquet):
    # DASH-04: curva de aprendizado = média de `correct` por número de tentativa (attempt_num
    # = cumcount por (SubjectID, AssignmentID) sobre Run.Program). Devolve uma série ordenada
    # por attempt_num crescente.
    from edmkt_app.eda import learning_curve

    curve = learning_curve(canonical_parquet)

    attempts = list(curve.keys())
    assert attempts == sorted(attempts)  # ordenada por número de tentativa
    assert attempts[0] in (0, 1)  # 1ª tentativa é o índice base (0 ou 1, contrato a fixar)
    for v in curve.values():
        assert 0.0 <= v <= 1.0


def test_compile_error_rate_by_assignment(canonical_parquet):
    # DASH-04 + WR-03: taxa de compile-error = Compile.Error POR tentativa de execução
    # (CE_count / Run_count), NÃO a fração sobre todos os eventos (CE/(CE+Run)). O stream
    # canônico preserva Compile.Error (clean.py:22); a439_mini tem >=1 (S2 c4).
    from edmkt_app.eda import compile_error_rate_by_assignment

    ce = compile_error_rate_by_assignment(canonical_parquet)

    assert 439 in ce
    assert ce[439] > 0.0  # o fixture tem ao menos um Compile.Error
    df = pd.read_parquet(canonical_parquet)
    ce_count = (df["EventType"] == "Compile.Error").sum()
    run_count = (df["EventType"] == "Run.Program").sum()
    expected = ce_count / run_count  # WR-03: denominador são SÓ os Run.Program
    assert ce[439] == pytest.approx(expected)
    # E a métrica corrigida NÃO coincide com a fórmula antiga (mistura de tipos): prova o fix.
    old_formula = (df["EventType"] == "Compile.Error").mean()
    assert ce[439] != pytest.approx(old_formula)
