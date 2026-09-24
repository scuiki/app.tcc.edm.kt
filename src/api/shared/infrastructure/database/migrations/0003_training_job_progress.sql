-- 0003 — progresso por-época do training_job (D-06): o que a CLI de treino escreve ao vivo.
-- Degrau forward-only: ALTER TABLE ADD COLUMN; o runner aplica DDL + user_version=3 na mesma txn.
-- As 6 colunas nascem NULL nas linhas pré-0003 (jobs sem progresso ainda escrito); a CLU escreve
-- explícito via update_progress/mark_*. Nenhuma toca a numérica do treino.
-- NOTA: o runner faz strip do comentário `--` antes do split por `;`; manter comentários em
-- linha própria — um `;` dentro de comentário inline racharia o split (WR-02).
ALTER TABLE training_job ADD COLUMN current_epoch INTEGER;
ALTER TABLE training_job ADD COLUMN total_epochs INTEGER;
ALTER TABLE training_job ADD COLUMN train_loss REAL;
ALTER TABLE training_job ADD COLUMN started_at TEXT;
ALTER TABLE training_job ADD COLUMN updated_at TEXT;
ALTER TABLE training_job ADD COLUMN error_message TEXT;
