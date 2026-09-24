"""Entrada do subprocess: `python -m edmkt_app.kc_pipeline --assignment N --job-id J`."""

from __future__ import annotations

import sys

from edmkt_app.background_jobs import worker_main
from edmkt_app.kc_pipeline.runner import _run_kc_pipeline


def main(argv: list[str] | None = None) -> int:
    return worker_main("edmkt_app.kc_pipeline", _run_kc_pipeline, argv)


if __name__ == "__main__":
    sys.exit(main())
