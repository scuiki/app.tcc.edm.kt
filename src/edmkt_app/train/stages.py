"""O corpo do treino: quadro de modelagem → cache de paths → train_and_evaluate → artefato.

`train_and_evaluate` é importado no topo de propósito: os testes o monkeypatcham AQUI para
simular falha e OOM de VRAM.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import torch

from edmkt_core.config import FROZEN_CONFIG
from edmkt_core.pipeline import split_by_subject, train_and_evaluate
from edmkt_core.seeding import set_global_seed

from edmkt_app import modeling_frame, provenance
from edmkt_app.features_cache import build_cache_on_disk, parse_rate
from edmkt_app.modeling_frame import load_modeling_frame
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.artifacts import ArtifactStore, flip_current
from edmkt_app import settings


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_epoch_writer(conn, job_id: int):
    def on_epoch(epoch: int, avg_loss: float) -> None:
        # Append, não UPDATE: sobrescrever destruía a curva a cada época (migração 0008).
        # Escrita curta sob WAL — o GET poll (D-04) lê concorrentemente sem bloquear.
        repos.TrainingMetricRepository(conn).append(
            job_id, epoch=epoch, train_loss=float(avg_loss), recorded_at=_now_iso()
        )

    return on_epoch


def _train_body(conn, assignment_id: int, job_id: int) -> dict:
    job_repo = repos.TrainingJobRepository(conn)

    total_epochs = FROZEN_CONFIG["epochs"]
    job_repo.mark_running(job_id, total_epochs=total_epochs, started_at=_now_iso())

    frame = load_modeling_frame(conn, assignment_id, data_root=settings.DATA_ROOT)
    df, turma_slug, progsnap_aid = frame.events, frame.turma_slug, frame.assignment_id

    train_df, test_df = split_by_subject(df)
    config = dict(FROZEN_CONFIG)

    # Aquece o cache de paths em disco (D-07): crash-safe, namespaced por turma, reaproveitado
    # no re-treino (Fase 7). A taxa de parse 3-vias (D-09) sai dos mesmos snapshots.
    code_states = dict(zip(df["CodeStateID"].astype(str), df["Code"].fillna("")))
    build_cache_on_disk(turma_slug, list(code_states.keys()), code_states, config)
    rate = parse_rate(list(code_states.values()), config)

    set_global_seed(config["seed"], strict=False)  # D-10: não-estrito na GPU, banda ±3pp
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # D-10/D-11

    result = train_and_evaluate(
        train_df,
        config=config,
        test_df=test_df,
        # Desembrulhado para int: edmkt_core é a camada congelada e compara com df["AssignmentID"]
        # — um VO aqui casaria com zero linhas em silêncio.
        assignment_id=progsnap_aid.value,
        device=device,
        on_epoch=_make_epoch_writer(conn, job_id),
        n_workers=None,
    )

    # Ordem load-bearing blob→INSERT→flip (Pitfall 2 artifacts): persist grava o v<N> e a
    # linha; flip_current só então aponta o ponteiro para um artefato já completo.
    persisted = ArtifactStore(str(settings.DATA_ROOT / turma_slug / "models")).persist(
        conn, frame.turma_id, assignment_id, result["model"], result["vocab"], config,
        first_auc=result["first_auc"],  # DASH-05: o AUC sobrevive ao subprocess via a linha (D-05)
        git_commit=provenance.git_commit(Path.cwd()),
        data_hash=provenance.file_hash(
            modeling_frame.canonical_parquet_path(settings.DATA_ROOT, turma_slug, progsnap_aid)
        ),
    )
    flip_current(conn, assignment_id, persisted["artifact_id"])
    conn.execute(
        "UPDATE assignment SET status='trained' WHERE id=?;", (assignment_id,)
    )  # D-03: assignment flipa só no fim
    # O dict de retorno some com o subprocess fire-and-forget; a linha SQLite é a ponte que
    # sobrevive ao término do filho — sem isto a taxa nunca chega ao GET (SC-3/MODEL-05).
    job_repo.mark_done(job_id, updated_at=_now_iso(), parse_rate=rate)

    return {
        "parse_rate": rate,
        "artifact_id": persisted["artifact_id"],
        "first_auc": result["first_auc"],
    }
