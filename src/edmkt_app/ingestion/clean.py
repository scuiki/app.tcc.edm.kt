"""Estágio C da ingestão: o stream de eventos canônico (D-10/D-11/D-12).

A ingestão é a DONA deste stream — foi verificado no código do núcleo que `edmkt_core` NÃO
filtra EventType (exceto `Run.Program` para a elegibilidade min_attempts em `split_by_subject`),
NÃO binariza o Score e NÃO trata CodeStateID órfão. Logo o dedup, a binarização e a integridade
referencial são responsabilidade EXCLUSIVA desta fase: sem esta limpeza explícita, "suporta
ProgSnap2" silenciosamente vira "suporta só o shape do CSEDM" (Pitfall 1).

Módulo puro (DataFrame-in → DataFrame canônico + avisos-out): sem I/O, sem SQL, sem edmkt_core.
Análogo EXATO: `../tcc.edm.kt/src/data_loader.py::filter_for_code_dkt`.
"""

from __future__ import annotations

import pandas as pd

from edmkt_app.ingestion.report import ReportItem
from edmkt_app.submission_events import KEPT_EVENTS, RUN_PROGRAM

# A tradução ProgSnap2 -> glossário acontece AQUI e só aqui: o CSV do professor chega com os
# nomes do padrão, e tudo o que vem depois (Parquet, EDA, treino, inferência) lê os nomes do
# glossário (docs/GLOSSARY.md, "Colunas do dado limpo").
PROGSNAP_TO_CLEANED_COLUMNS = {
    "SubjectID": "student_id",
    "AssignmentID": "progsnap_assignment_id",
    "ProblemID": "problem_id",
    "CodeStateID": "code_snapshot_id",
    "Code": "code",
    "Score": "score",
    "ServerTimestamp": "submitted_at",
    "EventType": "event_type",
}

# Contrato de colunas do dado limpo: exatamente o que build_sequences/train_and_evaluate consomem.
# A ordem é estável para o Parquet.
CANONICAL_COLUMNS = [*PROGSNAP_TO_CLEANED_COLUMNS.values(), "is_correct"]


def clean_event_stream(
    raw: pd.DataFrame, code_states: dict[str, str]
) -> tuple[pd.DataFrame, list[ReportItem]]:
    """Normaliza o DataFrame cru do ProgSnap2 no dado limpo, já com os nomes do glossário.

    Devolve (df_canônico, avisos). `code_states` é o dict {CodeStateID: Code} usado para o
    join do snapshot e a integridade referencial (D-11) — adicionados no estágio de integridade.
    """
    items: list[ReportItem] = []

    # Dedup/filtro (D-10): o filtro de EventType é o próprio tie-break do par mesmo-timestamp. No
    # ProgSnap2 do CSEDM cada Run.Program vem acompanhado de um Compile plain com o MESMO
    # ServerTimestamp e SEM Score; manter só {Run.Program, Compile.Error} descarta o plain.
    n_before = len(raw)
    df = raw[raw["EventType"].isin(KEPT_EVENTS)].copy()
    n_dropped = n_before - len(df)
    if n_dropped:
        items.append(
            ReportItem(
                check="dedup_compile",
                severity="warning",
                message=f"{n_dropped} evento(s) Compile plain descartado(s) no dedup mesmo-timestamp (D-10).",
                count=n_dropped,
            )
        )

    # Binarização (D-12) preservando o Score CONTÍNUO: `is_correct` é derivada à parte; a coluna
    # Score crua segue intacta para a EDA da Fase 6 (Pitfall 4 — não destruir o contínuo).
    df["is_correct"] = (
        (df["EventType"] == RUN_PROGRAM) & (df["Score"] == 1.0)
    ).astype(int)

    # Integridade referencial (D-11): evento cujo CodeStateID não existe em code_states não tem
    # snapshot para o núcleo extrair AST — é dropado e contado. Warning, não fatal: dado real tem
    # ruído e descartar < N eventos órfãos não invalida a turma. Só a contagem entra no ReportItem;
    # o `Code` cru do aluno NUNCA vai pra log/mensagem (Information Disclosure, T-03-09).
    known = set(code_states)
    mask_orphan = ~df["CodeStateID"].astype(str).isin(known)
    n_orphan = int(mask_orphan.sum())
    if n_orphan:
        df = df[~mask_orphan].copy()
        items.append(
            ReportItem(
                check="orphan_codestate",
                severity="warning",
                message=f"{n_orphan} evento(s) com CodeStateID órfão descartado(s) — sem snapshot em CodeStates (D-11).",
                count=n_orphan,
            )
        )

    # Join do snapshot por CodeStateID (análogo code_features.load_code_states): após o drop de
    # órfãos todo CodeStateID remanescente existe em code_states, então o map nunca produz NaN.
    df["Code"] = df["CodeStateID"].astype(str).map(code_states)

    cleaned = df.rename(columns=PROGSNAP_TO_CLEANED_COLUMNS)
    return cleaned[CANONICAL_COLUMNS].reset_index(drop=True), items
