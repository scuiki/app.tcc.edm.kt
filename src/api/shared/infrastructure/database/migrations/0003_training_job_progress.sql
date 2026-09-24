-- Progresso por época do training_job, o que a CLI de treino escreve ao vivo.
ALTER TABLE training_job ADD COLUMN current_epoch INTEGER;
ALTER TABLE training_job ADD COLUMN total_epochs INTEGER;
ALTER TABLE training_job ADD COLUMN train_loss REAL;
ALTER TABLE training_job ADD COLUMN started_at TEXT;
ALTER TABLE training_job ADD COLUMN updated_at TEXT;
ALTER TABLE training_job ADD COLUMN error_message TEXT;
