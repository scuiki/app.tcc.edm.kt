"""Commit atômico da ingestão: Parquet no FS + linhas no SQLite, sem meio-termo (D-06/D-13).

O FS não participa da transação do SQLite, então a ordem é load-bearing: os Parquet vão para
`.tmp`, os INSERTs rodam na transação, e só depois do COMMIT os temporários são renomeados para
o lugar. Nenhum caminho de falha é destrutivo — no pior caso sobra o Parquet anterior.

Separado de `service.py` porque é a única parte que toca o banco e o disco: o serviço decide
QUANDO persistir, este módulo sabe COMO.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from edmkt_app import data_layout
from edmkt_app.ingestion import clean
from edmkt_app.persistence import models, transaction
from edmkt_app.persistence import repositories as repos
from edmkt_app.values import TurmaSlug
from edmkt_app.clock import utc_now_iso





def _persist_atomic(
    conn,
    turma_name: str,
    canonical: pd.DataFrame,
    status_by_aid: dict[int, str],
) -> None:
    """Commit atômico (D-06): Parquet FORA da txn → INSERTs dentro; falha ⇒ rmtree + ROLLBACK.

    Ordem load-bearing (espelha artifacts.persist): primeiro grava o(s) Parquet do stream
    canônico (1 por AssignmentID, com as colunas exatas do seam edmkt_core — D-13), DEPOIS
    abre a transação e insere Turma → Assignments → Submissions pelas portas da Fase 2. Em
    QUALQUER exceção, o `transaction` faz ROLLBACK e nós removemos o diretório clean/ recém-
    escrito — sem dataset meio-gravado. O Parquet fica fora da txn porque um blob de FS não
    participa do ROLLBACK do SQLite; escrevê-lo dentro deixaria-o órfão num INSERT que falha.
    """
    turma_slug = TurmaSlug.from_name(turma_name)
    clean_dir = data_layout.cleaned_submissions_dir(turma_slug)
    created_at = utc_now_iso()

    # 1. Blob (Parquet) FORA da txn — um arquivo por AssignmentID, colunas do seam (D-13).
    #    Escrito em `.tmp` e só renomeado DEPOIS do COMMIT: `to_parquet` sobrescreve, então
    #    gravar direto no destino já destrói o Parquet anterior antes de saber se a transação
    #    vai passar, e o rollback (unlink) apagava o que sobrou — a turma ficava sem nada.
    #    Assim nenhum caminho de falha é destrutivo: no pior caso sobra o arquivo antigo.
    clean_dir.mkdir(parents=True, exist_ok=True)
    staged: list[tuple[Path, Path]] = []  # (tmp, destino final)
    try:
        for aid, group in canonical.groupby("AssignmentID", sort=True):
            pq_path = data_layout.cleaned_submissions_path(turma_slug, int(aid))
            tmp_path = pq_path.with_suffix(".parquet.tmp")
            # to_parquet via pyarrow; index=False mantém só as colunas canônicas no arquivo.
            group[clean.CANONICAL_COLUMNS].to_parquet(tmp_path, engine="pyarrow", index=False)
            staged.append((tmp_path, pq_path))

        # 2. INSERTs dentro de BEGIN IMMEDIATE/COMMIT (ROLLBACK-on-exception via db.transaction).
        with transaction(conn):
            turma_id = repos.TurmaRepository(conn).insert(
                models.Turma(id=None, name=turma_name, created_at=created_at)
            )
            assignment_repo = repos.AssignmentRepository(conn)
            submission_repo = repos.SubmissionRepository(conn)

            for aid, group in canonical.groupby("AssignmentID", sort=True):
                aid_int = int(aid)
                assignment_id = assignment_repo.insert(
                    models.Assignment(
                        id=None,
                        turma_id=turma_id,
                        name=f"Assignment {aid_int}",
                        current_version_id=None,
                        created_at=created_at,
                        # status do gate (D-08): trainable se ambas as classes; senão eda_only.
                        status=status_by_aid.get(aid_int, "eda_only"),
                    )
                )
                for row in group.itertuples(index=False):
                    submission_repo.insert(
                        models.Submission(
                            id=None,
                            assignment_id=assignment_id,
                            code_state_id=str(row.CodeStateID),
                            subject_id=None if pd.isna(row.SubjectID) else str(row.SubjectID),
                            problem_id=None if pd.isna(row.ProblemID) else int(row.ProblemID),
                            # Score REAL cru CONTÍNUO (Pitfall 4) — NUNCA o binário, NUNCA o Code
                            # (o snapshot fica só no Parquet/FS — Information Disclosure T-03-16).
                            score=None if pd.isna(row.Score) else float(row.Score),
                            created_at=created_at,
                            event_type=str(row.EventType),
                        )
                    )
    except BaseException:
        # ROLLBACK já desfez o SQLite; aqui só descartamos os temporários. Os Parquet que já
        # estavam no lugar nunca foram tocados — é o ponto do staging (D-06).
        for tmp_path, _dest in staged:
            tmp_path.unlink(missing_ok=True)
        raise

    # 3. Publicação: rename é atômico por arquivo e só acontece com a transação já commitada.
    #    Uma queda entre o COMMIT e o rename deixa o banco novo com o Parquet antigo — estado
    #    inconsistente, mas NÃO destrutivo, que é a troca certa quando o FS não participa da
    #    transação do SQLite. Um re-ingest reconstrói; um arquivo perdido, não.
    for tmp_path, dest in staged:
        tmp_path.replace(dest)
