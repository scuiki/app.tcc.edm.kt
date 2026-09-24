-- O schema passa a falar a língua do glossário, renomeando tabelas e colunas sem perder FKs.

ALTER TABLE turma RENAME TO classroom;
ALTER TABLE assignment RENAME COLUMN turma_id TO classroom_id;
ALTER TABLE assignment RENAME COLUMN current_version_id TO published_model_id;
ALTER TABLE submission RENAME COLUMN subject_id TO student_id;
ALTER TABLE submission RENAME COLUMN code_state_id TO code_snapshot_id;
ALTER TABLE mastery_prediction RENAME COLUMN subject_id TO student_id;
ALTER TABLE model_artifact RENAME COLUMN first_auc TO first_attempt_auc;

-- O AssignmentID do ProgSnap2 vira coluna, antes recuperado por regex do nome 'Assignment <N>'.
ALTER TABLE assignment ADD COLUMN progsnap_assignment_id INTEGER;
UPDATE assignment
SET progsnap_assignment_id = CAST(substr(name, length('Assignment ') + 1) AS INTEGER)
WHERE name LIKE 'Assignment %';

-- Os estados com nomes que enganavam ('trainable' era o passo antes de gerar KCs, não de treinar).
UPDATE assignment SET status = 'statistics_only' WHERE status = 'eda_only';
UPDATE assignment SET status = 'ready_for_kc_generation' WHERE status = 'trainable';

-- O progresso por época passa a viver em training_metric (0008).
ALTER TABLE training_job DROP COLUMN current_epoch;
ALTER TABLE training_job DROP COLUMN train_loss;
