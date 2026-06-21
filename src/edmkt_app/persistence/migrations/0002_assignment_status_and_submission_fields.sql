-- 0002 — assignment.status (estado treinável/EDA-only) + submission.event_type (stream canônico).
-- Degrau forward-only: ALTER TABLE ADD COLUMN; o runner aplica DDL + user_version=2 na mesma txn.
-- status é estado de PRIMEIRA CLASSE (D-05), não um booleano: 'eda_only' | 'trainable' (o gate de
-- viabilidade D-08/D-09 grava o veredito por-assignment, e o dashboard da Fase 6 depende dele).
-- Nasce NULL nas linhas pré-0002, mas a ingestão sempre grava explícito.
ALTER TABLE assignment ADD COLUMN status TEXT;
-- event_type = o tipo do evento do stream canônico pós-dedup (D-13): Run.Program | Compile.Error
-- (filtro D-10). O blob Code NÃO entra no SQLite — vai para Parquet/FS; aqui fica só o metadado.
ALTER TABLE submission ADD COLUMN event_type TEXT;
