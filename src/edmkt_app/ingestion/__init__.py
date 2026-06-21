"""Camada de ingestão de ProgSnap2 (fronteira impura, irmã de persistence/).

Public surface = a fronteira que a app FastAPI depende para dentro. Depende para dentro de
`edmkt_app.persistence` (portas da Fase 2) e do contrato de colunas do `edmkt_core`; o núcleo
científico (edmkt_core) é framework-free e NUNCA importa daqui. Este pacote é dono do stream
de eventos canônico (dedup/binarização/integridade — D-10/D-11/D-12) e de toda a escrita de
SQLite/Parquet da ingestão.

Por ora a surface expõe só o contrato de relatório (D-07); `service.ingest`/`detect_variants`
entram no plano 05 e crescem este __all__.
"""

from __future__ import annotations

from edmkt_app.ingestion.report import AssignmentSummary, IngestReport, ReportItem, Severity

__all__ = ["AssignmentSummary", "IngestReport", "ReportItem", "Severity"]
