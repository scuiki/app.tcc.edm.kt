-- Excluir uma turma marca deleted_at nela e nos assignments dela, e o resto fica como histórico.
ALTER TABLE classroom ADD COLUMN deleted_at TEXT;
ALTER TABLE assignment ADD COLUMN deleted_at TEXT;
