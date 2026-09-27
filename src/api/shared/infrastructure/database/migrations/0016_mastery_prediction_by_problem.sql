-- A matriz passa a ser por aluno e problema; as linhas por conceito saem e a leitura recalcula.
DROP TABLE mastery_prediction;
CREATE TABLE mastery_prediction (
    id INTEGER PRIMARY KEY,
    model_artifact_id INTEGER NOT NULL,
    student_id TEXT NOT NULL,
    problem_id INTEGER NOT NULL,
    mastery REAL,
    FOREIGN KEY (model_artifact_id) REFERENCES model_artifact (id)
);
CREATE UNIQUE INDEX uq_mastery_prediction ON mastery_prediction (model_artifact_id, student_id, problem_id);
