-- first_auc no model_artifact, o AUC que train.py já calcula e a 0009 renomeia depois.
ALTER TABLE model_artifact ADD COLUMN first_auc REAL;
