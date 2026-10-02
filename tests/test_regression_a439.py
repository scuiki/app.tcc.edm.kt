# Teste de regressão do Code-DKT no A439, a média de dez seeds da primeira tentativa em ±0,1 pp.

# Protege o PROCEDIMENTO (arquitetura, hiperparâmetros, ordem, seeds, deps), não pesos treinados.

# Marcado @pytest.mark.regression, fora do addopts padrão; roda quando ml ou as deps mudam.

# Sem EDMKT_CSEDM_PATH o fixture pula com motivo claro; o CSEDM nunca é copiado pro repo.

# As dez seeds se repetem bit a bit nesta máquina, então a faixa estreita pega qualquer mudança.

from __future__ import annotations

import pandas as pd
import pytest
import torch
from sklearn.model_selection import train_test_split

from ml.code_dkt.student_split import split_students_into_train_and_test
from ml.evaluation.seed_evaluation import evaluate_over_seeds
from ml.reproducibility.code_dkt_hyperparameters import CODE_DKT_HYPERPARAMETERS
from tests.fixtures.csedm import resolve_csedm_path


# O exercício do teste de regressão, o mesmo do repositório oficial.
A439 = 439

# A média das dez seeds da primeira tentativa que o app mediu no A439, em 02/10/2026
REGRESSION_CENTER = 0.7278
# Meio ponto de cada lado seria ruído entre seeds; aqui sobra só o ruído de float do ambiente
TOLERANCE = 0.001

BAND_LO = round(REGRESSION_CENTER - TOLERANCE, 4)  # 0.7268
BAND_HI = round(REGRESSION_CENTER + TOLERANCE, 4)  # 0.7288


def assert_in_band(first_auc: float, lo: float = BAND_LO, hi: float = BAND_HI) -> None:
    # Levanta AssertionError alto e claro, nomeando o valor observado e a faixa esperada.
    if not (lo <= first_auc <= hi):
        raise AssertionError(
            f"A média do first-attempt AUC, {first_auc:.4f}, saiu da faixa de regressão "
            f"[{lo:.4f}, {hi:.4f}] em torno de {REGRESSION_CENTER:.4f}. O código, as dependências "
            "ou o ambiente mudaram o comportamento do Code-DKT no A439."
        )


def test_band_fails_loud() -> None:
    # A guarda da faixa levanta erro fora dela e passa dentro; teste puro, sem dataset.
    assert_in_band(REGRESSION_CENTER)
    assert_in_band(BAND_LO)  # limite inferior incluso
    assert_in_band(BAND_HI)  # limite superior incluso

    for bad in (0.7266, 0.7290, 0.7595):
        with pytest.raises(AssertionError, match=r"saiu da faixa de regressão"):
            assert_in_band(bad)


def test_band_derives_from_the_measured_center() -> None:
    # A faixa é REGRESSION_CENTER ± TOLERANCE, os dois limites documentados, não números mágicos.
    assert (BAND_LO, BAND_HI) == (0.7268, 0.7288)


def test_regression_skipped_without_path(monkeypatch) -> None:
    # Sem EDMKT_CSEDM_PATH o fixture pula com motivo claro, prova o gate fast-by-default.
    monkeypatch.delenv("EDMKT_CSEDM_PATH", raising=False)
    with pytest.raises(pytest.skip.Exception):
        resolve_csedm_path()


@pytest.mark.regression
def test_a439_split_matches_the_official_repository(csedm_main_table) -> None:
    # O procedimento literal do src/preprocessing.py do repositório, sem treinar
    main_df = pd.read_csv(resolve_csedm_path() / "MainTable.csv")
    main_df = main_df[main_df["EventType"] == "Run.Program"]
    main_df = main_df[main_df["AssignmentID"] == 439]
    students = pd.unique(main_df["SubjectID"])
    repo_train, repo_test = train_test_split(students, test_size=0.2, random_state=1)

    train_df, test_df = split_students_into_train_and_test(
        csedm_main_table, progsnap_assignment_id=A439
    )

    assert len(students) == 386
    assert len(repo_test) == 78
    assert set(test_df["student_id"]) == set(repo_test)
    assert set(train_df["student_id"]) == set(repo_train)


@pytest.mark.regression
def test_regression_a439(csedm_main_table) -> None:
    # Retreina o A439 com as dez seeds, e a média da primeira tentativa precisa cair na faixa

    # A faixa foi medida na GPU, e na CPU a numérica é outra, então falha em vez de comparar
    if not torch.cuda.is_available():
        pytest.fail("O teste de regressão precisa da GPU, onde a faixa de ±0,1 ponto foi medida.")
    evaluation = evaluate_over_seeds(
        csedm_main_table, CODE_DKT_HYPERPARAMETERS, progsnap_assignment_id=A439,
        device=torch.device("cuda"),
    )

    by_seed = ", ".join(f"{s}={a:.4f}" for s, a in evaluation.first_attempt_auc_by_seed.items())
    print(
        f"\n[regression] A439 first-attempt AUC, média {evaluation.first_attempt_auc_mean:.4f} "
        f"(faixa [{BAND_LO:.4f}, {BAND_HI:.4f}]) por seed {by_seed}"
    )
    assert_in_band(evaluation.first_attempt_auc_mean)
