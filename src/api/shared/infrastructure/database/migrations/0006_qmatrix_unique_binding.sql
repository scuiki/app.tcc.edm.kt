-- 0006 — índice UNIQUE em qmatrix(assignment_id, kc_id, problem_id) (WR-04, KC-02/D-07).
-- Degrau forward-only: o runner aplica este DDL + user_version=6 na mesma txn (não bumpar aqui).
-- Torna real o `INSERT OR IGNORE`/`UPDATE OR IGNORE` de QMatrixRepository: sem este UNIQUE o
-- OR IGNORE não tem conflito a suprimir e se comporta como INSERT/UPDATE simples — add_kc/merge
-- duplicavam o trio (assignment, kc, problem), inflando kc_count_for_problem e a Q-matrix.
-- A semântica de binding é justamente "um par (problema, KC) existe ou não" — o trio é único.
-- NOTA: o runner faz strip do comentário `--` antes do split por `;` — manter comentários em
-- linha própria (mesma convenção do 0005).
CREATE UNIQUE INDEX uq_qmatrix_assignment_kc_problem
    ON qmatrix (assignment_id, kc_id, problem_id);
