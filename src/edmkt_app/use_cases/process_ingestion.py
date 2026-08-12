"""Processa a variante escolhida do upload: valida→limpa→viabilidade→persiste atômico (D-03)."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from edmkt_app.ingestion import service
from edmkt_app.ingestion.report import IngestReport
from edmkt_app.use_cases.base import BaseWriteUseCase


class ProcessIngestionDto(BaseModel):
    turma_name: str
    raw_dir: Path
    main_table: Path


class ProcessIngestionUseCase(BaseWriteUseCase):
    def _run(self, dto: ProcessIngestionDto) -> IngestReport:
        # O serviço segue dono da trava, do commit atômico e do rollback do blob — este use case
        # é a costura, não uma segunda implementação da ingestão.
        return service.ingest(self._conn, dto.raw_dir, dto.turma_name, dto.main_table)
