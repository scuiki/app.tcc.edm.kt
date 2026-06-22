"""CLI de treino headless: o corpo de treino isolado-por-processo (MODEL-01/02, D-01).

`python -m edmkt_app.train --assignment N --job-id J` é o processo OS que o handler FastAPI
(plano 04-04) dispara. Adquire a `PipelineLock` como PRIMEIRO ato (D-02) para que o
PID-liveness da Fase 2 recupere a trava se o treino morrer — o `holder_pid` precisa apontar
para o PID que realmente faz o trabalho, não para o web. Lê o Parquet canônico da Fase 3,
aquece o cache de paths em disco (plano 02), treina pelo seam congelado `train_and_evaluate`
injetando um `on_epoch` que grava progresso por-época, persiste o artefato versionado e flipa
`assignment.status` trainable→trained. Em falha o assignment segue `trainable`, o job marca
`failed` e o `with lock` libera a trava.

O subprocess abre a SUA conexão SQLite (`connect`), NUNCA compartilha objeto Python com o web
(Pitfall 2): a coordenação é só pela linha `pipeline_lock` + WAL. `edmkt_core` é só CHAMADO —
nenhum numeric é tocado (Pitfall 1).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import torch

from edmkt_core.config import FROZEN_CONFIG
from edmkt_core.pipeline import split_by_subject, train_and_evaluate
from edmkt_core.seeding import set_global_seed

from edmkt_app.features_cache import build_cache_on_disk, parse_rate
from edmkt_app.persistence import connect
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.artifacts import ArtifactStore, flip_current
from edmkt_app.persistence.lock import PipelineLock

# Raiz do FS de dados; resolvida em paths absolutos no main() para não depender do cwd
# herdado do web (Open Q2/A6). Override por teste.
DATA_ROOT = Path("data")
DB_PATH = "app.db"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(name: str) -> str:
    # Mesma forma de service._slug / features_cache._slug: o diretório da turma vem do slug
    # interno, nunca de nome de upload.
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "turma"


def _progsnap_aid(assignment_name: str) -> int:
    # O AssignmentID do ProgSnap2 (nome do Parquet) é o sufixo de "Assignment <N>" gravado
    # por service._persist_atomic. build_sequences também o consome.
    m = re.search(r"(\d+)", assignment_name)
    if m is None:
        raise ValueError(f"AssignmentID não derivável do nome: {assignment_name!r}")
    return int(m.group(1))


def _make_epoch_writer(conn, job_id: int):
    def on_epoch(epoch: int, avg_loss: float) -> None:
        # Escrita curta sob WAL — o GET poll (D-04) lê concorrentemente sem bloquear.
        repos.TrainingJobRepository(conn).update_progress(
            job_id, current_epoch=epoch, train_loss=float(avg_loss), updated_at=_now_iso()
        )

    return on_epoch


def _train_body(conn, assignment_id: int, job_id: int) -> dict:
    job_repo = repos.TrainingJobRepository(conn)
    asg_repo = repos.AssignmentRepository(conn)

    asg = asg_repo.get(assignment_id)
    if asg is None:
        raise ValueError(f"assignment {assignment_id} inexistente")
    turma = repos.TurmaRepository(conn).get(asg.turma_id)
    turma_slug = _slug(turma.name)
    progsnap_aid = _progsnap_aid(asg.name)

    total_epochs = FROZEN_CONFIG["epochs"]
    job_repo.mark_running(job_id, total_epochs=total_epochs, started_at=_now_iso())

    pq = DATA_ROOT / turma_slug / "clean" / f"assignment_{progsnap_aid}.parquet"
    df = pd.read_parquet(pq, engine="pyarrow")

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
        assignment_id=progsnap_aid,
        device=device,
        on_epoch=_make_epoch_writer(conn, job_id),
        n_workers=None,
    )

    # Ordem load-bearing blob→INSERT→flip (Pitfall 2 artifacts): persist grava o v<N> e a
    # linha; flip_current só então aponta o ponteiro para um artefato já completo.
    persisted = ArtifactStore(str(DATA_ROOT / turma_slug / "models")).persist(
        conn, asg.turma_id, assignment_id, result["model"], result["vocab"], config,
        first_auc=result["first_auc"],  # DASH-05: o AUC sobrevive ao subprocess via a linha (D-05)
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


def _run_training(conn, assignment_id: int, job_id: int) -> dict | None:
    """Adquire a trava (1º ato, D-02) e roda o treino; em falha marca o job e libera a trava.

    Retorna o dict de resultado (parse_rate/artifact_id/first_auc) no sucesso, ou None quando
    a trava está ocupada ou o treino falhou — o estado de falha vive todo no TrainingJob (D-03).
    """
    job_repo = repos.TrainingJobRepository(conn)
    lock = PipelineLock(conn).acquire("training", job_id=job_id)
    if not lock:
        job_repo.mark_failed(job_id, "pipeline busy")
        return None
    with lock:  # release garantido ao sair E sob exceção (SC3)
        try:
            return _train_body(conn, assignment_id, job_id)
        except torch.cuda.OutOfMemoryError:
            # D-11/Pitfall 4: VRAM da RTX 4050 (6 GB) estourou — falha com graça, sem detalhe
            # de tensor. O assignment segue trainable (nunca foi flipado).
            job_repo.mark_failed(
                job_id, "VRAM insuficiente para o treino; tente menos dados ou CPU"
            )
            return None
        except Exception as e:
            job_repo.mark_failed(job_id, str(e))
            return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m edmkt_app.train")
    parser.add_argument("--assignment", type=int, required=True, help="assignment.id (SQLite)")
    parser.add_argument("--job-id", type=int, required=True, help="training_job.id (SQLite)")
    args = parser.parse_args(argv)

    # Resolve paths absolutos a partir do env (não do cwd herdado, Open Q2/A6): o web e o
    # subprocess precisam ver o MESMO app.db e data/.
    global DATA_ROOT, DB_PATH
    DB_PATH = os.environ.get("EDMKT_DB_PATH", str(Path(DB_PATH).resolve()))
    DATA_ROOT = Path(os.environ.get("EDMKT_DATA_ROOT", str(DATA_ROOT.resolve())))

    conn = connect(DB_PATH)  # o subprocess abre a SUA conexão (Pitfall 2)
    result = _run_training(conn, args.assignment, args.job_id)
    return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())
