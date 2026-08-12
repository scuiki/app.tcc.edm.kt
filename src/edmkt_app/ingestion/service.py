"""Estágio E da ingestão — o ÚNICO módulo impuro: orquestra A→E e persiste atomicamente.

Costura os 4 estágios puros (discover/validate/clean/viability/summary) com a camada de
persistência da Fase 2 (repos + PipelineLock + Parquet). É aqui que o "validar tudo, depois
persistir" (D-06) e o "cru preservado + stream limpo normalizado" (D-13) viram comportamento
observável: pré-voo completo SEM tocar SQLite/Parquet, e só se `not report.has_fatal` a
persistência acontece.

Este módulo decide QUANDO persistir e é o dono da trava; o COMO (Parquet + INSERTs atômicos)
vive em `persist.py`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from edmkt_app import settings
from edmkt_app.ingestion import clean, discover, summary, validate, viability
from edmkt_app.ingestion.persist import _persist_atomic
from edmkt_app.ingestion.report import IngestReport, ReportItem
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.lock import PipelineLock

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    raw_dir = settings.DATA_ROOT / turma_slug / "raw"
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
