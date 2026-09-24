-- Série de loss por época (training_metric, append-only) e proveniência do artefato treinado.
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
