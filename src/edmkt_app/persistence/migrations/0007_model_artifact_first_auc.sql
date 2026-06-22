-- 0007 — first_auc no model_artifact (fecha o gap DASH-05 / D-05): a moldura de incerteza
-- (AUC + "dados de") precisa do AUC que train.py já calcula e hoje joga fora.
-- Degrau forward-only: ALTER TABLE ADD COLUMN; o runner aplica DDL + user_version=7 na mesma txn.
-- Nasce NULL nos artefatos pré-0007; train.py escreve explícito no persist do fim do treino.
-- D-05: só first_auc agora; all_auc fica adiado p/ a Fase 7 (re-treino/versionamento).
-- NOTA: o runner faz strip do comentário `--` antes do split por `;` — manter comentários em
-- linha própria; um `;` dentro de comentário inline racharia o split (WR-02).
ALTER TABLE model_artifact ADD COLUMN first_auc REAL;
