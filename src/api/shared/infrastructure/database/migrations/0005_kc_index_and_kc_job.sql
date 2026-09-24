-- kc.kc_index, o índice de cluster 0..N por assignment (o "kc_id científico" do TCC).
ALTER TABLE kc ADD COLUMN kc_index INTEGER;

-- kc_job espelha training_job, com 'stage' textual no lugar do progresso por época.
CREATE TABLE kc_job (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    stage TEXT,
    started_at TEXT,
    updated_at TEXT,
    error_message TEXT,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id)
);
