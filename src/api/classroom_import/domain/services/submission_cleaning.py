"""A limpeza do ProgSnap2 do professor: o dado limpo de onde tudo lê, com os nomes do glossário.

A importação é a DONA desta limpeza: o ml/ não filtra tipo de evento, não binariza o score e não
trata CodeStateID órfão. Sem esta etapa explícita, "suporta ProgSnap2" vira silenciosamente
"suporta só o formato do CSEDM". Três passos: descartar os eventos duplicados de mesmo timestamp,
derivar `is_correct` preservando o score contínuo, e descartar eventos sem snapshot de código.

Módulo puro (DataFrame entra, dado limpo + checagens saem): sem I/O, sem SQL, sem ml/.
"""

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.value_objects.import_report import ImportCheck
from api.classroom_import.domain.services.submission_event import KEPT_EVENTS, RUN_PROGRAM

# A tradução ProgSnap2 -> glossário acontece AQUI e só aqui: o CSV do professor chega com os
# nomes do padrão, e tudo o que vem depois (Parquet, estatísticas, treino, inferência) lê os nomes do
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

# Contrato de colunas do dado limpo: exatamente o que build_student_sequences/train_and_evaluate consomem.
# A ordem é estável para o Parquet.
CLEANED_COLUMNS = [*PROGSNAP_TO_CLEANED_COLUMNS.values(), "is_correct"]


def clean_submissions(
    raw: pd.DataFrame, code_by_snapshot: dict[str, str]
) -> tuple[pd.DataFrame, list[ImportCheck]]:
    """Normaliza o DataFrame cru do ProgSnap2 no dado limpo, já com os nomes do glossário.

    Devolve (dado limpo, avisos). `code_by_snapshot` é o dict {CodeStateID: Code} usado para o
    join do snapshot e a integridade referencial — adicionados no estágio de integridade.
    """
    checks: list[ImportCheck] = []

    # Dedup/filtro: o filtro de EventType é o próprio tie-break do par mesmo-timestamp. No
    # ProgSnap2 do CSEDM cada Run.Program vem acompanhado de um Compile plain com o MESMO
    # ServerTimestamp e SEM Score; manter só {Run.Program, Compile.Error} descarta o plain.
    n_before = len(raw)
    df = raw[raw["EventType"].isin(KEPT_EVENTS)].copy()
    n_dropped = n_before - len(df)
    if n_dropped:
        checks.append(
            ImportCheck(
                check="dedup_compile",
                severity="warning",
                message=f"{n_dropped} evento(s) Compile plain descartado(s) no dedup mesmo-timestamp.",
                count=n_dropped,
            )
        )

    # Binarização preservando o Score CONTÍNUO: `is_correct` é derivada à parte; a coluna
    # Score crua segue intacta para as estatísticas pré-treino.
    df["is_correct"] = (
        (df["EventType"] == RUN_PROGRAM) & (df["Score"] == 1.0)
    ).astype(int)

    # Integridade referencial: evento cujo CodeStateID não existe em code_by_snapshot não tem
    # snapshot para o núcleo extrair AST — é dropado e contado. Warning, não fatal: dado real tem
    # ruído e descartar < N eventos órfãos não invalida a turma. Só a contagem entra no ImportCheck;
    # o `Code` cru do aluno NUNCA vai pra log/mensagem.
    known = set(code_by_snapshot)
    mask_orphan = ~df["CodeStateID"].astype(str).isin(known)
    n_orphan = int(mask_orphan.sum())
    if n_orphan:
        df = df[~mask_orphan].copy()
        checks.append(
            ImportCheck(
                check="orphan_codestate",
                severity="warning",
                message=f"{n_orphan} evento(s) com CodeStateID órfão descartado(s) — sem snapshot em CodeStates.",
                count=n_orphan,
            )
        )

    # Join do snapshot por CodeStateID (análogo code_features.load_code_states): após o drop de
    # órfãos todo CodeStateID remanescente existe em code_by_snapshot, então o map nunca produz NaN.
    df["Code"] = df["CodeStateID"].astype(str).map(code_by_snapshot)

    cleaned = df.rename(columns=PROGSNAP_TO_CLEANED_COLUMNS)
    return cleaned[CLEANED_COLUMNS].reset_index(drop=True), checks
