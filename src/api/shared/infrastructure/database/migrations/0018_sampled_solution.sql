-- As soluções que a extração escolheu para o LLM ler, pela execução e pela posição no prompt.
CREATE TABLE sampled_solution (
    assignment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    submission_id INTEGER NOT NULL,
    PRIMARY KEY (assignment_id, problem_id, position),
    FOREIGN KEY (assignment_id, problem_id) REFERENCES problem (assignment_id, problem_id),
    FOREIGN KEY (submission_id) REFERENCES submission (id)
);
