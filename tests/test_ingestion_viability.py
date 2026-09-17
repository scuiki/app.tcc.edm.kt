"""Testes herméticos do gate de viabilidade por-assignment (D-08/D-09 RESOLVIDO).

Pinam a política RESOLVIDA: o único bloqueio duro (trainable=False / EDA-only) é a ausência de
ambas as classes nos first-attempts (AUC matematicamente indefinido). Pisos de problemas/amostra
NUNCA derrubam trainable — viram avisos graduados severity="viability". A fixture de classe única
(`ingest_single_class_df`) exercita o caso intestável no dataset de referência (Pitfall 2).
"""

from __future__ import annotations

import pandas as pd

from edmkt_app.ingestion.report import AssignmentSummary, ReportItem
from edmkt_app.ingestion.viability import assess_viability


def _item(items: list[ReportItem], check: str) -> ReportItem | None:
    return next((i for i in items if i.check == check), None)


def test_a439_mini_ambas_as_classes_e_trainable(a439_mini):
    summaries, items = assess_viability(a439_mini)

    assert len(summaries) == 1
    s = summaries[0]
    assert isinstance(s, AssignmentSummary)
    assert s.assignment_id == 439
    assert s.both_classes_present is True
    # both_classes_present é o ÚNICO bloqueio duro (D-09): presentes => trainable.
    assert s.trainable is True


def test_classe_unica_bloqueia_duro_com_reason(ingest_single_class_df):
    summaries, items = assess_viability(ingest_single_class_df)

    assert len(summaries) == 1
    s = summaries[0]
    assert s.both_classes_present is False
    # Único bloqueio científico: AUC indefinido => EDA-only (D-09).
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
                    "SubjectID": sid,
                    "AssignmentID": 439,
                    "ProblemID": 1,  # 1 problema só => few_problems
                    "ServerTimestamp": base + pd.Timedelta(minutes=10 * i + k),
                    "EventType": "Run.Program",
                    "Score": score if k == 0 else 1.0,
                    "CodeStateID": f"{sid}-{k}",
                    "Code": "public int f(){return 1;}",
                    "correct": int(score == 1.0) if k == 0 else 1,
                }
            )
    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")

    summaries, items = assess_viability(df)
    s = summaries[0]

    fp = _item(items, "few_problems")
    assert fp is not None
    assert fp.severity == "viability"
    # O piso de problemas é AVISO, não parede: classe presente => trainable permanece.
    assert s.both_classes_present is True
    assert s.trainable is True


def test_small_sample_avisa_mas_nao_bloqueia():
    # Poucos alunos elegíveis (3), ambas as classes presentes => aviso small_sample,
    # trainable inalterado (governado só por classe — D-09).
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for i, (sid, score) in enumerate([("S1", 0.0), ("S2", 1.0), ("S3", 1.0)]):
        for k in range(3):
            pid = 1 + k  # >=2 problemas => não dispara few_problems
            rows.append(
                {
                    "SubjectID": sid,
                    "AssignmentID": 439,
                    "ProblemID": pid,
                    "ServerTimestamp": base + pd.Timedelta(minutes=10 * i + k),
                    "EventType": "Run.Program",
                    "Score": score if k == 0 else 1.0,
                    "CodeStateID": f"{sid}-{k}",
                    "Code": "public int f(){return 1;}",
                    "correct": int(score == 1.0) if k == 0 else 1,
                }
            )
    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")

    summaries, items = assess_viability(df)
    s = summaries[0]

    ss = _item(items, "small_sample")
    assert ss is not None
    assert ss.severity == "viability"
    assert s.trainable is True  # aviso não derruba


def test_n_students_eligible_conta_so_min_3_run_program():
    # S1 com 3 RP (elegível), S2 com 2 RP (NÃO elegível) — espelha split_by_subject.
    base = pd.Timestamp("2019-03-01T08:00:00Z")
    rows = []
    for k in range(3):
        rows.append(
            {
                "SubjectID": "S1",
                "AssignmentID": 439,
                "ProblemID": 1 + k,
                "ServerTimestamp": base + pd.Timedelta(minutes=k),
                "EventType": "Run.Program",
                "Score": 0.0 if k == 0 else 1.0,
                "CodeStateID": f"S1-{k}",
                "Code": "x",
                "correct": 0 if k == 0 else 1,
            }
        )
    for k in range(2):  # S2 abaixo do piso de elegibilidade
        rows.append(
            {
                "SubjectID": "S2",
                "AssignmentID": 439,
                "ProblemID": 1 + k,
                "ServerTimestamp": base + pd.Timedelta(hours=1, minutes=k),
                "EventType": "Run.Program",
                "Score": 1.0,
                "CodeStateID": f"S2-{k}",
                "Code": "x",
                "correct": 1,
            }
        )
    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")

    summaries, _ = assess_viability(df)
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
                "SubjectID": sid,
                "AssignmentID": 439,
                "ProblemID": 1,
                "ServerTimestamp": base,
                "EventType": "Run.Program",
                "Score": score,
                "CodeStateID": f"{sid}-439",
                "Code": "x",
                "correct": int(score == 1.0),
            }
        )
    # A492: todos acertam => uma classe só.
    for sid in ["S3", "S4"]:
        rows.append(
            {
                "SubjectID": sid,
                "AssignmentID": 492,
                "ProblemID": 1,
                "ServerTimestamp": base,
                "EventType": "Run.Program",
                "Score": 1.0,
                "CodeStateID": f"{sid}-492",
                "Code": "x",
                "correct": 1,
            }
        )
    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")

    summaries, _ = assess_viability(df)
    by_id = {s.assignment_id: s for s in summaries}
    assert by_id[439].trainable is True
    assert by_id[492].trainable is False
