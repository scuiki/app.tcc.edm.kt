-- O dado limpo (código Java inclusive) sai do Parquet e passa a morar todo em submission.
DROP TABLE submission;  -- numa instalação com dado real, os Parquets migram para cá antes disto

-- student_id e code_snapshot_id ficam sem tipo declarado, o SQLite guarda o valor como veio.
CREATE TABLE submission (
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
    FOREIGN KEY (assignment_id) REFERENCES assignment (id)
);

CREATE INDEX idx_submission_assignment ON submission (assignment_id);
