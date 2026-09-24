-- A tabela dos vínculos problema e KC deixa o nome da literatura e passa a dizer o que guarda.
ALTER TABLE qmatrix RENAME TO problem_kc;
DROP INDEX uq_qmatrix_assignment_kc_problem;
CREATE UNIQUE INDEX uq_problem_kc ON problem_kc (assignment_id, kc_id, problem_id);
