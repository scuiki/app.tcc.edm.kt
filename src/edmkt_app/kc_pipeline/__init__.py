"""Pipeline KCGen-KT headless, isolado por processo (KC-01/KC-04, D-04/D-05).

`python -m edmkt_app.kc_pipeline --assignment N --job-id J` é o processo OS que o handler
FastAPI dispara. Espelha `train.py`: trava como primeiro ato, lê o Parquet canônico da Fase 3
por AssignmentID do ProgSnap2 (Pitfall 3), filtra as amostras primeira-correta (Pitfall 4),
roda o pipeline puro (`edmkt_core.kc`) pelo transporte `claude` com cache, valida o conteúdo
(KC-04) e, no sucesso, persiste kc+qmatrix atomicamente e flipa o status para `kc_draft` (D-06).

O subprocess abre a SUA conexão SQLite, NUNCA compartilha objeto Python com o web (Pitfall 2):
a coordenação é só pela linha `pipeline_lock` + WAL. `edmkt_core.kc` é só ORQUESTRADO — o
transporte LLM é injetado pela porta (DIP).

Divisão: `settings` (o modelo pinado) · `transport` (porta LLM + cache) · `stages` (os estágios)
· `qmatrix_validation` (a guarda KC-04) · `__main__` (trava + CLI).
"""
