-- 0004 — taxa de parse por-assignment no training_job (D-06 estendido / MODEL-05).
-- Degrau forward-only: ALTER TABLE ADD COLUMN; o runner aplica DDL + user_version=4 na mesma txn.
-- Fecha o BLOCKER do SC-3: a taxa era calculada em train.py e jogada fora com o subprocess;
-- agora tem coluna onde gravar e sobreviver ao término do processo filho.
-- Nasce NULL nas linhas pré-0004 (jobs sem treino concluído); o subprocess escreve explícito.
-- NOTA: o runner faz strip do comentário `--` antes do split por `;`; manter comentários em
-- linha própria — um `;` dentro de comentário inline racharia o split (WR-02).
ALTER TABLE training_job ADD COLUMN parse_rate REAL;
