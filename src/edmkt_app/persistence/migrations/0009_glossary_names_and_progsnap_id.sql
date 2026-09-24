-- 0009 — o schema passa a falar a língua do glossário (docs/GLOSSARY.md).
--
-- Nomes de tabela abreviados continuam (kc, kc_job, qmatrix, model_artifact); o que muda são os
-- nomes que carregavam um conceito com outro nome no código. RENAME TABLE/COLUMN preserva as FKs
-- e os índices que apontam para eles (SQLite >= 3.26, sem legacy_alter_table).

ALTER TABLE turma RENAME TO classroom;
ALTER TABLE assignment RENAME COLUMN turma_id TO classroom_id;
ALTER TABLE assignment RENAME COLUMN current_version_id TO published_model_id;
ALTER TABLE submission RENAME COLUMN subject_id TO student_id;
ALTER TABLE submission RENAME COLUMN code_state_id TO code_snapshot_id;
ALTER TABLE mastery_prediction RENAME COLUMN subject_id TO student_id;
ALTER TABLE model_artifact RENAME COLUMN first_auc TO first_attempt_auc;

-- O AssignmentID do ProgSnap2 vira coluna. Antes era recuperado por regex do nome, que a
-- importação sempre gravou como 'Assignment <N>'.
ALTER TABLE assignment ADD COLUMN progsnap_assignment_id INTEGER;
UPDATE assignment
SET progsnap_assignment_id = CAST(substr(name, length('Assignment ') + 1) AS INTEGER)
WHERE name LIKE 'Assignment %';

-- Os estados com nomes que enganavam: 'trainable' era o passo antes de gerar KCs, não de treinar.
UPDATE assignment SET status = 'statistics_only' WHERE status = 'eda_only';
UPDATE assignment SET status = 'ready_for_kc_generation' WHERE status = 'trainable';

-- Resíduo da 0008: o progresso por época vive em training_metric.
ALTER TABLE training_job DROP COLUMN current_epoch;
ALTER TABLE training_job DROP COLUMN train_loss;
