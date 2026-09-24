-- Schema inicial, as entidades do domínio mais a trava de pipeline de uma linha só.

CREATE TABLE turma (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- current_version_id nasce NULL e só vira o ModelArtifact publicado após um artefato completo.
CREATE TABLE assignment (
    id INTEGER PRIMARY KEY,
    turma_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    current_version_id INTEGER,
    created_at TEXT NOT NULL,
    FOREIGN KEY (turma_id) REFERENCES turma (id),
    FOREIGN KEY (current_version_id) REFERENCES model_artifact (id)
);

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

-- content_hash é dedup/integridade, não identidade (pode colidir com seed fixo), nunca é a PK.
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

CREATE TABLE kc (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id)
);

CREATE TABLE qmatrix (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    kc_id INTEGER NOT NULL,
    problem_id INTEGER NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id),
    FOREIGN KEY (kc_id) REFERENCES kc (id)
);

CREATE TABLE mastery_prediction (
    id INTEGER PRIMARY KEY,
    model_artifact_id INTEGER NOT NULL,
    subject_id TEXT NOT NULL,
    kc_id INTEGER NOT NULL,
    mastery REAL,
    FOREIGN KEY (model_artifact_id) REFERENCES model_artifact (id),
    FOREIGN KEY (kc_id) REFERENCES kc (id)
);

CREATE TABLE training_job (
    id INTEGER PRIMARY KEY,
    assignment_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (assignment_id) REFERENCES assignment (id)
);

-- CHECK(id = 1) faz da trava um singleton, holder_pid NULL quer dizer trava livre.
CREATE TABLE pipeline_lock (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    holder_pid INTEGER,
    operation TEXT,
    job_id INTEGER,
    acquired_at TEXT
);

INSERT INTO pipeline_lock (id, holder_pid, operation, job_id, acquired_at)
VALUES (1, NULL, NULL, NULL, NULL);
