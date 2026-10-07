-- O nome que a extração gerou, em inglês e em minúsculas, ao lado do nome em português
ALTER TABLE kc ADD COLUMN generated_name TEXT;

-- Onde cada conceito aparece numa solução amostrada do problema, pela primeira e última linha
CREATE TABLE kc_evidence (
    assignment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    kc_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    first_line INTEGER NOT NULL,
    last_line INTEGER NOT NULL,
    PRIMARY KEY (assignment_id, problem_id, kc_id),
    FOREIGN KEY (assignment_id, problem_id, position)
        REFERENCES sampled_solution (assignment_id, problem_id, position),
    FOREIGN KEY (kc_id) REFERENCES kc (id)
);
