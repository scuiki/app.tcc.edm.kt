# Teste de regressão contra a execução de referência do TCC 1, A439 first-attempt AUC em ±3pp.

# Protege o PROCEDIMENTO (arquitetura, hiperparâmetros, ordem, seed, deps), não pesos treinados.

# Marcado @pytest.mark.regression, fora do addopts padrão; roda quando ml ou as deps mudam.

# Sem EDMKT_CSEDM_PATH o fixture pula com motivo claro; o CSEDM nunca é copiado pro repo.

# O check multi-seed mais pesado fica fora daqui por design, este é o gate de 1 treino no nitro.

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
    # Resolve EDMKT_CSEDM_PATH ou pula o teste; o CSEDM real nunca é copiado pro repo, só apontado.
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

# Declarações Java mínimas e compiláveis; parse_member_declaration aceita, gera >=1 AST path.
_JAVA_OK_A = "public int f(int x) { return x + 1; }"
_JAVA_OK_B = "public int g(int a, int b) { int s = a + b; return s; }"
_JAVA_OK_C = "public boolean h(int n) { if (n > 0) { return true; } return false; }"
# Java deliberadamente malformado, exercita a guarda try/except contra DoS (devolve []).
_JAVA_BAD = "public int oops( { return ;;; }"
# Faz parse mas não tem par de folhas; extract_ast_paths devolve [] sem levantar exceção.
_JAVA_EMPTY_CLASS = "class C {}"


@pytest.fixture
def csedm_main_table() -> pd.DataFrame:
    # CSEDM Spring 2019 real, moldado pro seam público train_and_evaluate.

    # Só eventos Run.Program (filtro que o Code-DKT do TCC 1 treinou), correto é Score == 1.0.

    # Reproduz a partição de referência (random_state=1, min_attempts=3), como no TCC 1.
    data_dir = _resolve_csedm_path()

    df = pd.read_csv(data_dir / "MainTable.csv")
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True, errors="coerce")
    df["AssignmentID"] = pd.to_numeric(df["AssignmentID"], errors="coerce").astype("Int64")
    df["ProblemID"] = pd.to_numeric(df["ProblemID"], errors="coerce").astype("Int64")

    # Só Run.Program + label binário (o filtro exato que o TCC 1 usou pra treinar o Code-DKT).
    df = df[df["EventType"] == "Run.Program"].copy()
    df["correct"] = (df["Score"] == 1.0).astype(int)

    # Junta o snapshot Java por evento (CodeStateID -> Code), pro seam ver código inline.
    code_states = pd.read_csv(data_dir / "CodeStates" / "CodeStates.csv")
    code_map = dict(zip(code_states["CodeStateID"].astype(str), code_states["Code"].fillna("")))
    df["Code"] = df["CodeStateID"].astype(str).map(code_map).fillna("")

    # Mesma tradução que o import aplica (ingestion/clean); daqui em diante, nomes do glossário.
    from api.classroom_import.domain.services.submission_cleaning import PROGSNAP_TO_CLEANED_COLUMNS

    df = df.rename(columns={**PROGSNAP_TO_CLEANED_COLUMNS, "correct": "is_correct"})
    return df.reset_index(drop=True)

# Partição de referência do TCC 1.
A439 = 439

# Execução de referência do TCC 1, Code-DKT A439 first-attempt AUC (comparison_summary.json).
REFERENCE_AUC = 0.732654
# Tolerância de 3pp absorve a variância de seed (~1,34pp no TCC 1) e o gap hidden_dim 128 vs 200.
TOLERANCE_PP = 0.03

BAND_LO = round(REFERENCE_AUC - TOLERANCE_PP, 4)  # 0.7027
BAND_HI = round(REFERENCE_AUC + TOLERANCE_PP, 4)  # 0.7627


def assert_in_band(first_auc: float, lo: float = BAND_LO, hi: float = BAND_HI) -> None:
    # Levanta AssertionError alto e claro, nomeando o valor observado e a banda esperada.
    if not (lo <= first_auc <= hi):
        raise AssertionError(
            f"first-attempt AUC {first_auc:.4f} is OUTSIDE the regression band "
            f"[{lo:.4f}, {hi:.4f}] (reference run {REFERENCE_AUC:.4%} ±3pp). "
            f"A dependency, seed, or operation-order change moved A439 out of band."
        )


def test_band_fails_loud() -> None:
    # A guarda da banda levanta erro fora do range e passa dentro; teste puro, sem dataset.
    assert_in_band(0.7300)  # dentro da banda, não levanta
    assert_in_band(BAND_LO)  # limite inferior incluso
    assert_in_band(BAND_HI)  # limite superior incluso

    for bad in (0.50, 0.90):
        with pytest.raises(AssertionError, match=r"OUTSIDE the regression band"):
            assert_in_band(bad)


def test_band_derives_from_reference() -> None:
    # A banda é REFERENCE_AUC ± TOLERANCE_PP, os dois limites documentados, não números mágicos.
    assert BAND_LO == 0.7027
    assert BAND_HI == 0.7627


def test_regression_skipped_without_path(monkeypatch) -> None:
    # Sem EDMKT_CSEDM_PATH o fixture pula com motivo claro, prova o gate fast-by-default.
    monkeypatch.delenv("EDMKT_CSEDM_PATH", raising=False)
    with pytest.raises(pytest.skip.Exception):
        _resolve_csedm_path()


@pytest.mark.regression
def test_regression_a439(csedm_main_table) -> None:
    # Retreina A439 no CSEDM real; first-attempt AUC precisa cair em [0.7027, 0.7627].

    # Reproduz a partição do TCC 1 (random_state=1, min_attempts=3) e roda o seam público.
    train_df, test_df = split_students_into_train_and_test(
        csedm_main_table, test_size=0.2, random_state=1, min_attempts=3
    )

    # Não estrito na GPU, confia na banda de ±3pp em vez de pagar o custo do determinismo bit a bit.
    seed_all_random_generators(CODE_DKT_HYPERPARAMETERS["seed"], strict=False)

    result = train_and_evaluate(
        train_df, CODE_DKT_HYPERPARAMETERS, test_df, progsnap_assignment_id=A439
    )

    first_auc = result["first_attempt_auc"]
    print(f"\n[regression] A439 first-attempt AUC = {first_auc:.4f} "
          f"(band [{BAND_LO:.4f}, {BAND_HI:.4f}], reference run {REFERENCE_AUC:.4%})")
    assert_in_band(first_auc)
