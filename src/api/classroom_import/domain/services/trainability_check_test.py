"""Testes herméticos do gate de viabilidade por-assignment.

Pinam a política RESOLVIDA: o único bloqueio duro (trainable=False / EDA-only) é a ausência de
ambas as classes nos first-attempts (AUC matematicamente indefinido). Pisos de problemas/amostra
NUNCA derrubam trainable — viram avisos graduados severity="viability". A fixture de classe única
(`ingest_single_class_df`) exercita o caso intestável no dataset de referência.
"""

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.value_objects.import_report import (
    AssignmentTrainability,
    ImportCheck,
)
from api.classroom_import.domain.services.trainability_check import check_assignment_trainability


def _item(items: list[ImportCheck], check: str) -> ImportCheck | None:
    return next((i for i in items if i.check == check), None)


def test_a439_mini_ambas_as_classes_e_trainable(a439_mini):
    summaries, items = check_assignment_trainability(a439_mini)

    assert len(summaries) == 1
    s = summaries[0]
    assert isinstance(s, AssignmentTrainability)
    assert s.progsnap_assignment_id == 439
    assert s.both_classes_present is True
    # both_classes_present é o ÚNICO bloqueio duro: presentes => trainable.
    assert s.trainable is True


def test_classe_unica_bloqueia_duro_com_reason(ingest_single_class_df):
    summaries, items = check_assignment_trainability(ingest_single_class_df)

    assert len(summaries) == 1
    s = summaries[0]
    assert s.both_classes_present is False
    # Único bloqueio científico: AUC indefinido => EDA-only.
    assert s.trainable is False
    # A reason precisa nomear a causa (classe ausente / AUC indefinido) — anti-silencioso.
    assert any("classe" in r.lower() or "auc" in r.lower() for r in s.reasons)


def test_few_problems_avisa_mas_nao_bloqueia():
    # 1 problema só, mas com AMBAS as classes nos first-attempts (S1 erra, S2 acerta).
    # min_attempts>=3 Run.Program por aluno: 3 RP cada para serem elegíveis.
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for i, (sid, score) in enumerate([("S1", 0.0), ("S2", 1.0), ("S3", 1.0)]):
        for k in range(3):
            rows.append(
                {
                    "student_id": sid,
                    "progsnap_assignment_id": 439,
                    "problem_id": 1,  # 1 problema só => few_problems
                    "submitted_at": base + pd.Timedelta(minutes=10 * i + k),
                    "event_type": "Run.Program",
                    "score": score if k == 0 else 1.0,
                    "code_snapshot_id": f"{sid}-{k}",
                    "code": "public int f(){return 1;}",
                    "is_correct": int(score == 1.0) if k == 0 else 1,
                }
            )
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")

    summaries, items = check_assignment_trainability(df)
    s = summaries[0]

    fp = _item(items, "few_problems")
    assert fp is not None
    assert fp.severity == "viability"
    # O piso de problemas é AVISO, não parede: classe presente => trainable permanece.
    assert s.both_classes_present is True
    assert s.trainable is True


def test_small_sample_avisa_mas_nao_bloqueia():
    # Poucos alunos elegíveis (3), ambas as classes presentes => aviso small_sample,
    # trainable inalterado (governado só por classe).
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for i, (sid, score) in enumerate([("S1", 0.0), ("S2", 1.0), ("S3", 1.0)]):
        for k in range(3):
            pid = 1 + k  # >=2 problemas => não dispara few_problems
            rows.append(
                {
                    "student_id": sid,
                    "progsnap_assignment_id": 439,
                    "problem_id": pid,
                    "submitted_at": base + pd.Timedelta(minutes=10 * i + k),
                    "event_type": "Run.Program",
                    "score": score if k == 0 else 1.0,
                    "code_snapshot_id": f"{sid}-{k}",
                    "code": "public int f(){return 1;}",
                    "is_correct": int(score == 1.0) if k == 0 else 1,
                }
            )
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")

    summaries, items = check_assignment_trainability(df)
    s = summaries[0]

    ss = _item(items, "small_sample")
    assert ss is not None
    assert ss.severity == "viability"
    assert s.trainable is True  # aviso não derruba


def test_n_students_eligible_conta_so_min_3_run_program():
    # S1 com 3 RP (elegível), S2 com 2 RP (NÃO elegível) — espelha split_students_into_train_and_test.
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for k in range(3):
        rows.append(
            {
                "student_id": "S1",
                "progsnap_assignment_id": 439,
                "problem_id": 1 + k,
                "submitted_at": base + pd.Timedelta(minutes=k),
                "event_type": "Run.Program",
                "score": 0.0 if k == 0 else 1.0,
                "code_snapshot_id": f"S1-{k}",
                "code": "x",
                "is_correct": 0 if k == 0 else 1,
            }
        )
    for k in range(2):  # S2 abaixo do piso de elegibilidade
        rows.append(
            {
                "student_id": "S2",
                "progsnap_assignment_id": 439,
                "problem_id": 1 + k,
                "submitted_at": base + pd.Timedelta(hours=1, minutes=k),
                "event_type": "Run.Program",
                "score": 1.0,
                "code_snapshot_id": f"S2-{k}",
                "code": "x",
                "is_correct": 1,
            }
        )
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")

    summaries, _ = check_assignment_trainability(df)
    s = summaries[0]
    # Só S1 tem >=3 Run.Program; S2 é excluído da contagem de elegíveis (não bloqueia).
    assert s.n_students_eligible == 1


def test_gate_por_assignment_independente():
    # A439 com ambas as classes (trainable) e A492 com uma classe só (EDA-only) na mesma turma.
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    # A439: S1 erra, S2 acerta nos first-attempts => ambas as classes.
    for sid, score in [("S1", 0.0), ("S2", 1.0)]:
        rows.append(
            {
                "student_id": sid,
                "progsnap_assignment_id": 439,
                "problem_id": 1,
                "submitted_at": base,
                "event_type": "Run.Program",
                "score": score,
                "code_snapshot_id": f"{sid}-439",
                "code": "x",
                "is_correct": int(score == 1.0),
            }
        )
    # A492: todos acertam => uma classe só.
    for sid in ["S3", "S4"]:
        rows.append(
            {
                "student_id": sid,
                "progsnap_assignment_id": 492,
                "problem_id": 1,
                "submitted_at": base,
                "event_type": "Run.Program",
                "score": 1.0,
                "code_snapshot_id": f"{sid}-492",
                "code": "x",
                "is_correct": 1,
            }
        )
    df = pd.DataFrame(rows)
    df["submitted_at"] = pd.to_datetime(df["submitted_at"], utc=True)
    df["progsnap_assignment_id"] = df["progsnap_assignment_id"].astype("Int64")
    df["problem_id"] = df["problem_id"].astype("Int64")

    summaries, _ = check_assignment_trainability(df)
    by_id = {s.progsnap_assignment_id: s for s in summaries}
    assert by_id[439].trainable is True
    assert by_id[492].trainable is False
