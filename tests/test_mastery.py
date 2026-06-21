"""Testes RED de mastery (DASH-01/02/03) — invariantes, não números mágicos.

Pinam o contrato do módulo puro `edmkt_core.mastery` ANTES de existir (Nyquist: a
implementação dos planos 02-06 nasce GREEN contra estes testes). Filosofia herdada de
test_artifacts.py: asseritar invariantes (ordenação, faixas nos limites, média problem→KC,
regra de risco) em vez de valores específicos de um modelo treinado. Todos FALHAM agora com
ImportError em `edmkt_core.mastery` — é o estado Wave 0 esperado.

A matriz aluno×KC é construída tomando a ÚLTIMA correct_predictions por (user_id, ProblemID)
e fazendo a MÉDIA sobre os problemas que cada KC marca (via Q-matrix) — NUNCA indexando a
saída do modelo por kc_id (Pitfall 2: a cabeça do Code-DKT é por ProblemID, não por KC).
"""

from __future__ import annotations

import pandas as pd
import pytest


def test_bands_classify_at_boundaries():
    # DASH-01: faixas fixas low <0.40 / medium 0.40–0.70 / high >0.70 (prototype, REQUIREMENTS:85).
    # Os limites são o que importa: 0.40 é o piso de medium, 0.70 o teto de medium.
    from edmkt_core.mastery import classify_band

    assert classify_band(0.0) == "low"
    assert classify_band(0.399) == "low"
    assert classify_band(0.40) == "medium"  # limite inferior pertence a medium
    assert classify_band(0.55) == "medium"
    assert classify_band(0.70) == "medium"  # 0.70 ainda é medium; só >0.70 vira high
    assert classify_band(0.7001) == "high"
    assert classify_band(1.0) == "high"


def test_matrix_aggregates_problem_to_kc_by_mean():
    # DASH-01 + Pitfall 2: a mastery de um KC é a MÉDIA das masteries dos problemas que o KC
    # marca. Q-matrix: KC1 → {prob 1, prob 3}; KC2 → {prob 2, prob 3}.
    # Para um aluno com problem-mastery {1: 0.2, 2: 0.8, 3: 0.6}:
    #   KC1 = mean(0.2, 0.6) = 0.4 ; KC2 = mean(0.8, 0.6) = 0.7.
    from edmkt_core.mastery import build_mastery_matrix

    # pred_df no shape de predict_code_dkt: a ÚLTIMA linha por (user_id, ProblemID) é a mastery
    # final daquele problema; uma 1ª tentativa anterior NÃO deve sobrescrever a última.
    pred_df = pd.DataFrame(
        [
            {"user_id": "S1", "skill_name": "1", "correct": 0, "is_first_attempt": True,  "correct_predictions": 0.9},
            {"user_id": "S1", "skill_name": "1", "correct": 0, "is_first_attempt": False, "correct_predictions": 0.2},  # última p/ prob 1
            {"user_id": "S1", "skill_name": "2", "correct": 1, "is_first_attempt": True,  "correct_predictions": 0.8},
            {"user_id": "S1", "skill_name": "3", "correct": 1, "is_first_attempt": True,  "correct_predictions": 0.6},
        ]
    )
    qmatrix = {1: [10], 2: [20], 3: [10, 20]}  # problem_id -> [kc_id...]; KC1=10, KC2=20

    matrix = build_mastery_matrix(pred_df, qmatrix)

    # matrix indexável por (subject_id, kc_id) -> mastery float em [0,1].
    assert matrix[("S1", 10)] == pytest.approx(0.4)  # mean(0.2 [última do prob1], 0.6)
    assert matrix[("S1", 20)] == pytest.approx(0.7)  # mean(0.8, 0.6)


def test_critical_kcs_ascending_by_mean_class_mastery(trained_artifact):
    # DASH-02: KCs críticos = ordenados por mastery MÉDIA da turma, ASCENDENTE (o mais fraco
    # primeiro). Duas turmas sintéticas: KC 'A' média 0.2, KC 'B' média 0.8 → A vem antes de B.
    from edmkt_core.mastery import critical_kcs

    matrix = {
        ("S1", 1): 0.1, ("S2", 1): 0.3,  # KC 1 média 0.2
        ("S1", 2): 0.7, ("S2", 2): 0.9,  # KC 2 média 0.8
    }
    ranked = critical_kcs(matrix)

    kc_order = [kc_id for kc_id, _mean in ranked]
    assert kc_order == [1, 2]  # ascendente: o KC de menor mastery média primeiro
    assert ranked[0][1] == pytest.approx(0.2)
    assert ranked[1][1] == pytest.approx(0.8)


def test_at_risk_students_below_low_band(trained_artifact):
    # DASH-03: aluno em atenção = tem >= N KCs abaixo da faixa low (<0.40). N=3 travado pelo
    # prototype (A4). S_risk tem 3 KCs <0.40 (entra); S_ok tem só 2 (não entra).
    from edmkt_core.mastery import at_risk_students

    matrix = {
        ("S_risk", 1): 0.1, ("S_risk", 2): 0.2, ("S_risk", 3): 0.3, ("S_risk", 4): 0.9,
        ("S_ok",   1): 0.1, ("S_ok",   2): 0.2, ("S_ok",   3): 0.8, ("S_ok",   4): 0.9,
    }
    at_risk = at_risk_students(matrix, threshold_n=3)

    assert "S_risk" in at_risk
    assert "S_ok" not in at_risk
