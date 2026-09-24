-- Índice UNIQUE em qmatrix, torna real o INSERT/UPDATE OR IGNORE de QMatrixRepository.
CREATE UNIQUE INDEX uq_qmatrix_assignment_kc_problem
    ON qmatrix (assignment_id, kc_id, problem_id);
