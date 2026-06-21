"""Camada de ingestão de ProgSnap2 (fronteira impura, irmã de persistence/).

Public surface = a fronteira que a app FastAPI depende para dentro. Depende para dentro de
`edmkt_app.persistence` (portas da Fase 2) e do contrato de colunas do `edmkt_core`; o núcleo
científico (edmkt_core) é framework-free e NUNCA importa daqui. Este pacote é dono do stream
de eventos canônico (dedup/binarização/integridade — D-10/D-11/D-12) e de toda a escrita de
SQLite/Parquet da ingestão.

A surface expõe o contrato de relatório (D-07) e a fronteira impura do orquestrador
(`service.ingest`/`service.detect_variants`) — os pontos de entrada que a app FastAPI consome.
"""

from __future__ import annotations

from edmkt_app.ingestion.report import AssignmentSummary, IngestReport, ReportItem, Severity
from edmkt_app.ingestion.service import detect_variants, ingest

__all__ = [
    "AssignmentSummary",
    "IngestReport",
    "ReportItem",
    "Severity",
    "detect_variants",
    "ingest",
]
