"""Testes herméticos do resumo do dataset + preview da MainTable (INGEST-02).

`build_summary` deriva as 4 contagens de visão geral (alunos/assignments/problemas/submissões)
sobre o stream canônico. `build_preview` devolve as primeiras N linhas CRUAS da MainTable SEM o
snapshot `Code` cru do aluno (Information Disclosure — T-03-12).
"""

from __future__ import annotations

import pandas as pd

from edmkt_app.ingestion.summary import build_preview, build_summary


def test_build_summary_a439_mini(a439_mini):
    s = build_summary(a439_mini)

    assert s["n_students"] == 3  # S1, S2, S_long
    assert s["n_assignments"] == 1  # tudo no A439
    assert s["n_problems"] == 3  # problemas 1, 2, 3
    assert s["n_submissions"] == len(a439_mini)


def test_build_preview_omite_code_cru(a439_mini):
    preview = build_preview(a439_mini, n=2)

    assert isinstance(preview, list)
    assert len(preview) == 2
    assert all(isinstance(r, dict) for r in preview)
    # Nenhum dict do preview pode carregar o snapshot `Code` cru do aluno (T-03-12).
    assert all("Code" not in r for r in preview)
    # Metadados úteis seguem presentes para os cards de visão geral.
    assert all("SubjectID" in r for r in preview)


def test_build_preview_respeita_n():
    rows = [
        {
            "SubjectID": f"S{i}",
            "AssignmentID": 439,
            "ProblemID": 1,
            "EventType": "Run.Program",
            "Score": 1.0,
            "ServerTimestamp": pd.Timestamp("2019-03-01T08:00:00Z"),
            "CodeStateID": f"c{i}",
            "Code": "public int f(){return 1;}",
        }
        for i in range(20)
    ]
    df = pd.DataFrame(rows)

    assert len(build_preview(df, n=5)) == 5
    # n maior que o dataset não estoura: devolve o que existe.
    assert len(build_preview(df, n=999)) == 20
