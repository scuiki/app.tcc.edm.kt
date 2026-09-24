"""CLI de treino headless: o corpo de treino isolado-por-processo (MODEL-01/02, D-01).

`python -m edmkt_app.train --assignment N --job-id J` é o processo OS que o handler FastAPI
dispara. Adquire a `OneJobAtATimeLock` como PRIMEIRO ato (D-02) para que o PID-liveness da Fase 2
recupere a trava se o treino morrer — o `holder_pid` precisa apontar para o PID que realmente
faz o trabalho, não para o web. Toma o quadro de modelagem pronto de `modeling_frame` (nunca o
Parquet cru — training-serving skew), aquece o cache de paths, treina pelo seam congelado
`train_and_evaluate` injetando um `on_epoch` que APPENDA o progresso por época, persiste o
artefato versionado e flipa `assignment.status` para `trained`.

O subprocess abre a SUA conexão SQLite, NUNCA compartilha objeto Python com o web (Pitfall 2).
`ml` é só CHAMADO — nenhum numeric é tocado (Pitfall 1).

Divisão espelhando kc_pipeline: `settings` · `stages` (o corpo) · `runner` (trava + falha) ·
`__main__` (CLI).
"""
