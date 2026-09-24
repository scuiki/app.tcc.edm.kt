-- 0008 — série de loss por época + proveniência do artefato.
-- Antes: update_progress fazia UPDATE em training_job.train_loss, então cada época destruía a
-- anterior e sobrava um número só. A curva de loss, figura padrão em trabalho de ML, não era
-- plotável a partir do que ficava guardado.
-- training_metric é append-only: o progresso corrente passa a ser DERIVADO da última linha, em
-- vez de um campo mutável que existe em paralelo à verdade.
-- git_commit/data_hash respondem "qual código e qual dado produziram esta versão" — hoje o banco
-- tem dois artefatos com AUC diferente e nenhum registro do que mudou entre eles.
-- Forward-only; nascem NULL nos artefatos anteriores.
-- NOTA: o runner faz strip do comentário `--` antes do split por `;` — manter comentários em
-- linha própria; um `;` dentro de comentário inline racharia o split (WR-02).
CREATE TABLE training_metric (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL,
    epoch INTEGER NOT NULL,
    train_loss REAL NOT NULL,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES training_job (id),
    UNIQUE (job_id, epoch)
);
CREATE INDEX idx_training_metric_job ON training_metric (job_id, epoch);
ALTER TABLE model_artifact ADD COLUMN git_commit TEXT;
ALTER TABLE model_artifact ADD COLUMN data_hash TEXT;
