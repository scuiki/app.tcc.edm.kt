-- 0005 — coluna kc.kc_index + tabela kc_job para o pipeline KCGen-KT (D-06/Open Q2, KC-01).
-- Degrau forward-only: o runner aplica este DDL + user_version=5 na mesma txn (não bumpar aqui).
-- kc_index = id do cluster 0..N por-assignment (o "kc_id científico" do TCC); permite round-trip
-- fiel com results/kc_clusters_A*.json + qmatrix_A*.csv, onde kc.id do banco é autoincrement
-- global enquanto kc_index é o índice de cluster que o replay de referência compara (Open Q2). Nasce NULL nas
-- linhas pré-0005 e nos KCs criados manualmente pelo professor (KC-02); o pipeline grava explícito.
-- assignment.status já é TEXT (degrau 0002) — os novos valores 'kc_draft'/'kc_approved' (D-06) NÃO
-- exigem DDL, só strings novas + a troca do guard de treino; nenhuma coluna nova de assignment aqui.
-- kc_job espelha training_job (0001): linha de estado do job de background lida por polling GET,
-- com 'stage' textual (sample/generate/cluster/label/qmatrix) no lugar do progresso por-época.
-- NOTA: o runner faz strip do comentário `--` antes do split por `;` — manter comentários em
-- linha própria; um `;` dentro de comentário inline racharia o split (WR-02).
ALTER TABLE kc ADD COLUMN kc_index INTEGER;

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
