-- Os KCs que o LLM listou em cada problema, na ordem da resposta, e o conceito em que caíram
CREATE TABLE candidate_kc (
    assignment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    position INTEGER NOT NULL,
    name TEXT NOT NULL,
    reasoning TEXT NOT NULL,
    -- A justificativa em português, que a tradução da extração preenche
    translated_reasoning TEXT,
    kc_id INTEGER NOT NULL,
    PRIMARY KEY (assignment_id, problem_id, position),
    FOREIGN KEY (assignment_id, problem_id) REFERENCES problem (assignment_id, problem_id),
    FOREIGN KEY (kc_id) REFERENCES kc (id)
);

-- O modelo de linguagem e a versão do prompt de cada extração
ALTER TABLE kc_job ADD COLUMN model_id TEXT;
ALTER TABLE kc_job ADD COLUMN prompt_version TEXT;
