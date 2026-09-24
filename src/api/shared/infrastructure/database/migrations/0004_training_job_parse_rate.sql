-- Taxa de parse por assignment no training_job, gravada pelo subprocess ao fim do treino.
ALTER TABLE training_job ADD COLUMN parse_rate REAL;
