-- 0001 — initial schema: the 8 domain entities (D-01) + the one-row pipeline lock.
-- foreign_keys is enabled on the CONNECTION (db.py), NOT here (RESEARCH §0001).
-- kc / qmatrix / mastery_prediction are born MINIMAL (PK + FKs + the 1-2 columns SC4
-- exercises) and grow via ALTER TABLE in phases 5-6.

-- Turma (class).
CREATE TABLE turma (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Assignment. current_version_id points at the published ModelArtifact (D-06); it is born
-- NULL and gets flipped atomically only after a complete artifact is written + inserted.
CREATE TABLE assignment (
    id INTEGER PRIMARY KEY,
    turma_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    current_version_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (turma_id) REFERENCES turma (id),
    FOREIGN KEY (current_version_id) REFERENCES model_artifact (id)
);

-- Submission: one ProgSnap2 code state for an assignment.
CREATE TABLE submission (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    code_state_id TEXT NOT NULL,
    subject_id TEXT,
    problem_id INTEGER,
    score REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id)
);

-- ModelArtifact: write-once trained model on the FS, referenced by path (CLAUDE.md §Persistence).
-- version_number is monotonic per (assignment); UNIQUE is the safety net for the
-- MAX(version_number)+1 race (D-04 / RESEARCH Pitfall 5). content_hash is integrity/dedup,
-- NOT identity (it can collide under seed=42) — so it is a plain column, never the PK.
CREATE TABLE model_artifact (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    version_number INTEGER NOT NULL,
    content_hash TEXT,
    artifact_dir TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id),
    UNIQUE (assignment_id, version_number)
);

-- KC (knowledge component) — minimal; grows in phase 5.
CREATE TABLE kc (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id)
);

-- Q-matrix entry (problem x KC) — minimal; grows in phase 5.
CREATE TABLE qmatrix (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    kc_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id),
    FOREIGN KEY (kc_id) REFERENCES kc (id)
);

-- MasteryPrediction (student x KC mastery) — minimal; grows in phase 6.
CREATE TABLE mastery_prediction (
    id INTEGER PRIMARY KEY,
    model_artifact_id INTEGER NOT NULL,
    subject_id TEXT NOT NULL,
    kc_id INTEGER NOT NULL,
    mastery REAL,
    FOREIGN KEY (model_artifact_id) REFERENCES model_artifact (id),
    FOREIGN KEY (kc_id) REFERENCES kc (id)
);

-- TrainingJob: status of a background training run — minimal.
CREATE TABLE training_job (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id)
);

-- Pipeline lock: a dedicated ONE-row table (RESEARCH Open Q3). CHECK(id=1) makes it a
-- singleton; holder_pid NULL means the lock is free.
CREATE TABLE pipeline_lock (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    holder_pid INTEGER,
    operation TEXT,
    job_id INTEGER,
    acquired_at TEXT
);

-- Seed the single free lock row.
INSERT INTO pipeline_lock (id, holder_pid, operation, job_id, acquired_at)
VALUES (1, NULL, NULL, NULL, NULL);
