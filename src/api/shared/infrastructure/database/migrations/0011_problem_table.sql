-- Os problemas ganham tabela própria, e submission e qmatrix passam a apontar para ela.
CREATE TABLE problem (
    assignment_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    description TEXT,
    PRIMARY KEY (assignment_id, problem_id),
    FOREIGN KEY (assignment_id) REFERENCES assignment (id)
);

INSERT INTO problem (assignment_id, problem_id)
SELECT DISTINCT assignment_id, problem_id FROM submission WHERE problem_id IS NOT NULL
UNION
SELECT DISTINCT assignment_id, problem_id FROM qmatrix;

-- O SQLite não acrescenta FK a uma tabela existente, então cada uma é recriada e copiada.
CREATE TABLE submission_with_problem (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    student_id,
    problem_id INTEGER,
    code_snapshot_id,
    code TEXT,
    score REAL,
    submitted_at TEXT NOT NULL,
    event_type TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id),
    FOREIGN KEY (assignment_id, problem_id) REFERENCES problem (assignment_id, problem_id)
);

INSERT INTO submission_with_problem
    (id, assignment_id, student_id, problem_id, code_snapshot_id, code, score, submitted_at,
     event_type, is_correct)
SELECT id, assignment_id, student_id, problem_id, code_snapshot_id, code, score, submitted_at,
       event_type, is_correct
FROM submission;

DROP TABLE submission;
ALTER TABLE submission_with_problem RENAME TO submission;
CREATE INDEX idx_submission_assignment ON submission (assignment_id);

CREATE TABLE qmatrix_with_problem (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    kc_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id),
    FOREIGN KEY (kc_id) REFERENCES kc (id),
    FOREIGN KEY (assignment_id, problem_id) REFERENCES problem (assignment_id, problem_id)
);

INSERT INTO qmatrix_with_problem (id, assignment_id, kc_id, problem_id)
SELECT id, assignment_id, kc_id, problem_id FROM qmatrix;

DROP TABLE qmatrix;
ALTER TABLE qmatrix_with_problem RENAME TO qmatrix;
CREATE UNIQUE INDEX uq_qmatrix_assignment_kc_problem ON qmatrix (assignment_id, kc_id, problem_id);
