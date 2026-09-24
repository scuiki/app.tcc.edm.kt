-- assignment.status é estado de primeira classe, não booleano ('eda_only' ou 'trainable').
ALTER TABLE assignment ADD COLUMN status TEXT;
-- event_type é o tipo do evento pós-dedup; o código Java não entra aqui, vai para Parquet/FS.
ALTER TABLE submission ADD COLUMN event_type TEXT;
