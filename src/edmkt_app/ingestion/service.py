"""Estágio E da ingestão — o ÚNICO módulo impuro: orquestra A→E e persiste atomicamente.

Costura os 4 estágios puros (discover/validate/clean/viability/summary) com a camada de
persistência da Fase 2 (repos + PipelineLock + Parquet). É aqui que o "validar tudo, depois
persistir" (D-06) e o "cru preservado + stream limpo normalizado" (D-13) viram comportamento
observável: pré-voo completo SEM tocar SQLite/Parquet, e só se `not report.has_fatal` grava
Turma + Assignments (status trainable/eda_only) + Submissions pelas portas da Fase 2 e o
stream canônico em Parquet. Em qualquer falha o Parquet recém-escrito é removido e a transação
faz ROLLBACK — sem datasets meio-gravados.

Análogo EXATO do commit atômico: `persistence/artifacts.py::ArtifactStore.persist` — blob
(Parquet) escrito FORA da txn; a txn cobre só os INSERTs; em falha, ROLLBACK + rmtree do blob.
A ordem é load-bearing: blob → INSERTs (espelha CR-01 da Fase 2).
"""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from edmkt_app.ingestion import clean, discover, summary, validate, viability
from edmkt_app.ingestion.report import IngestReport, ReportItem
from edmkt_app.persistence import models, transaction
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import PipelineLock

# Raiz do FS de dados. Override por teste/deploy; default relativo ao cwd (data/<turma>/...).
DATA_ROOT = Path("data")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(name: str) -> str:
    # Componente de caminho derivado de um nome arbitrário do professor: minúsculas, só
    # [a-z0-9_-], colapsando o resto em "-". NUNCA usar o nome de membro do zip como caminho
    # (Security T-03-15); o slug interno é a única fonte do diretório da turma.
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "turma"


def _empty_report(items: list[ReportItem]) -> IngestReport:
    # Relatório que NÃO persistiu nada (busy ou fatal no pré-voo): contagens zeradas, sem
    # per_assignment nem preview. has_fatal continua governado por `items`.
    return IngestReport(
        items=items,
        dataset_summary={"n_students": 0, "n_assignments": 0, "n_problems": 0, "n_submissions": 0},
        per_assignment=[],
        main_table_preview=[],
    )


def detect_variants(zip_path: Path, turma_slug: str) -> dict:
    """Extrai o `.zip` em data/<turma_slug>/raw/ e devolve as variantes de layout (D-03).

    READ-ONLY do ponto de vista do estado COMPARTILHADO: NÃO adquire a PipelineLock (Lock
    Timing) — prendê-la aqui a manteria presa durante a escolha humana de variante. Só escreve
    em data/<turma_slug>/raw/, estado privado deste upload (preserva o cru — D-13). Devolve o
    dict de discover.detect_variants acrescido de `raw_dir` para o caminho de processamento.
    """
    raw_dir = DATA_ROOT / turma_slug / "raw"
    discover.extract_zip(Path(zip_path), raw_dir)
    variants = discover.detect_variants(raw_dir)
    variants["raw_dir"] = raw_dir
    return variants


def _load_code_states(raw_dir: Path) -> dict[str, str]:
    # {CodeStateID: Code} para o join do snapshot + integridade referencial (D-11). Análogo
    # code_features.load_code_states. Ausência de CodeStates ⇒ dict vazio: o clean trata todo
    # CodeStateID como órfão (warning), nunca explode.
    cs_path = discover.find_code_states(Path(raw_dir))
    if cs_path is None:
        return {}
    cs_df = pd.read_csv(cs_path, encoding="utf-8-sig")
    return dict(zip(cs_df["CodeStateID"].astype(str), cs_df["Code"].fillna("")))


def ingest(
    conn,
    raw_dir: Path,
    turma_name: str,
    chosen_main_table: Path,
) -> IngestReport:
    """Caminho de PROCESSAMENTO: A→E sob a trava, com commit atômico (D-06/D-13/Lock Timing).

    Adquire a PipelineLock AQUI (não na detecção): a trava protege o estado COMPARTILHADO
    (SQLite/FS), que só é tocado a partir da persistência. Trava ocupada por dono vivo ⇒
    devolve relatório "busy" sem persistir. Dentro do `with lock:` roda validate → (fatal ⇒
    aborta sem persistir, D-06) → clean → assess_viability → build_summary/preview, depois
    persiste atomicamente. O `with` garante release ao sair, inclusive sob exceção (SC3).
    """
    lock = PipelineLock(conn).acquire("ingestion", job_id=None)
    if not lock:
        # _DENIED é falsy ⇒ "pipeline busy"; nada persiste, nenhuma trava setada por nós.
        return _empty_report(
            [
                ReportItem(
                    check="pipeline_busy",
                    severity="fatal",
                    message="Já existe um processamento em andamento. Aguarde a conclusão e tente novamente.",
                )
            ]
        )

    with lock:
        return _ingest_locked(conn, Path(raw_dir), turma_name, Path(chosen_main_table))


def _ingest_locked(
    conn,
    raw_dir: Path,
    turma_name: str,
    chosen_main_table: Path,
) -> IngestReport:
    items: list[ReportItem] = []

    # B. Pré-voo de falhas duras (INGEST-01). Qualquer fatal ⇒ DataFrame None.
    main_df, validate_items = validate.validate(chosen_main_table)
    items.extend(validate_items)
    if main_df is None:
        # D-05 nível 1 / D-06: falha dura no pré-voo ⇒ NADA persiste.
        return _empty_report(items)

    # C. Stream canônico (dedup/binarização/integridade). O join do Code usa o CodeStates do raw.
    code_states = _load_code_states(raw_dir)
    canonical, clean_items = clean.clean_event_stream(main_df, code_states)
    items.extend(clean_items)

    # D. Gate de viabilidade por-assignment (D-08/D-09). per_assignment carrega o trainable.
    per_assignment, viability_items = viability.assess_viability(canonical)
    items.extend(viability_items)

    # Visão geral (INGEST-02): contagens do stream canônico + preview cru da MainTable (sem Code).
    dataset_summary = summary.build_summary(canonical)
    main_table_preview = summary.build_preview(main_df)

    report = IngestReport(
        items=items,
        dataset_summary=dataset_summary,
        per_assignment=per_assignment,
        main_table_preview=main_table_preview,
    )

    # E. Persistência atômica. Mapeia trainable por AssignmentID (ProgSnap2) do gate.
    status_by_aid = {
        s.assignment_id: ("trainable" if s.trainable else "eda_only") for s in per_assignment
    }
    _persist_atomic(conn, turma_name, canonical, status_by_aid)
    return report


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
    slug = _slug(turma_name)
    clean_dir = DATA_ROOT / slug / "clean"
    created_at = _now_iso()

    # 1. Blob (Parquet) FORA da txn — um arquivo por AssignmentID, colunas do seam (D-13).
    clean_dir.mkdir(parents=True, exist_ok=True)
    parquet_written: list[Path] = []
    try:
        for aid, group in canonical.groupby("AssignmentID", sort=True):
            pq_path = clean_dir / f"assignment_{int(aid)}.parquet"
            # to_parquet via pyarrow; index=False mantém só as colunas canônicas no arquivo.
            group[clean.CANONICAL_COLUMNS].to_parquet(pq_path, engine="pyarrow", index=False)
            parquet_written.append(pq_path)

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
        # ROLLBACK já desfez o SQLite; aqui desfazemos o blob recém-escrito (rmtree do clean/),
        # espelhando o rmtree do rollback de artifacts.persist — sem resto parcial (D-06).
        for pq in parquet_written:
            if pq.exists():
                pq.unlink()
        raise
