"""Entrada do subprocess: `python -m edmkt_app.train --assignment N --job-id J`."""

from __future__ import annotations

import sys

from api.shared.infrastructure.background_jobs import worker_main
from edmkt_app.train.runner import _run_training


def main(argv: list[str] | None = None) -> int:
    return worker_main("edmkt_app.train", _run_training, argv)


if __name__ == "__main__":
    sys.exit(main())
