"""Entrada do subprocess: `python -m edmkt_app.train --assignment N --job-id J`."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from edmkt_app.persistence import connect
from edmkt_app.train import settings
from edmkt_app.train.runner import _run_training


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m edmkt_app.train")
    parser.add_argument("--assignment", type=int, required=True, help="assignment.id (SQLite)")
    parser.add_argument("--job-id", type=int, required=True, help="training_job.id (SQLite)")
    args = parser.parse_args(argv)

    # Resolve paths absolutos a partir do env (não do cwd herdado, Open Q2/A6): o web e o
    # subprocess precisam ver o MESMO app.db e data/.
    settings.DB_PATH = os.environ.get("EDMKT_DB_PATH", str(Path(settings.DB_PATH).resolve()))
    settings.DATA_ROOT = Path(os.environ.get("EDMKT_DATA_ROOT", str(settings.DATA_ROOT.resolve())))

    conn = connect(settings.DB_PATH)  # o subprocess abre a SUA conexão (Pitfall 2)
    result = _run_training(conn, args.assignment, args.job_id)
    return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())
