-- Remover um KC ou um vínculo passa a marcar a linha com deleted_at, e o histórico fica no banco.
ALTER TABLE kc ADD COLUMN deleted_at TEXT;
ALTER TABLE problem_kc ADD COLUMN deleted_at TEXT;
-- O índice único vale só para vínculos ativos, então religar um vínculo removido cria outra linha
DROP INDEX uq_problem_kc;
CREATE UNIQUE INDEX uq_problem_kc ON problem_kc (assignment_id, kc_id, problem_id)
    WHERE deleted_at IS NULL;
