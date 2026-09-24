-- 0010 — o dado limpo passa a morar no SQLite, na tabela submission.
--
-- Antes ele ficava num Parquet por assignment, e a tabela submission guardava uma cópia só dos
-- metadados que ninguém lia. Agora a tabela tem tudo (o código Java inclusive) e é a única fonte:
-- a importação grava numa transação só, e treino, dashboard e geração de KCs leem daqui.
--
-- A tabela antiga é descartada, porque cada linha dela está no Parquet, com mais colunas.
-- Numa instalação que já tem dados, os Parquets são copiados para cá por um script avulso,
-- conferido linha a linha, antes de serem apagados.
--
-- student_id e code_snapshot_id ficam SEM tipo declarado: o SQLite guarda o valor como veio
-- (número no CSEDM, texto em outro dataset), como o Parquet fazia.

DROP TABLE submission;

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
