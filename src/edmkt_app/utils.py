"""Helpers internos puros compartilhados pela app layer (IN-01).

`run_program_only` é o recorte do stream canônico para a stack de modelagem (treino e
inferência): dois call sites e uma razão que não pode se perder numa expressão solta repetida.

Derivação de caminho e de id migrou para `values.py` — `slug`/`progsnap_aid` viraram
`TurmaSlug`/`ProgSnapAssignmentId`, porque o problema nunca foi onde a função morava e sim
haver seis cópias dela; um tipo não se copia por engano.

Mantido livre de torch/persistence (igual a eda.py): import barato, sem acoplar a stack de ML.
"""

from __future__ import annotations

import pandas as pd

# O Parquet canônico da Fase 3 guarda {Run.Program, Compile.Error} de propósito — o filtro de
# EventType É o dedup do par de mesmo timestamp (clean.py D-10) e a EDA precisa dos compile
# errors para a taxa de erro. Modelagem é outra história: o TCC 1 treinou o Code-DKT só sobre
# Run.Program, e é esse o dado que o golden-run usa como oráculo.
RUN_EVENT = "Run.Program"


def run_program_only(df: pd.DataFrame) -> pd.DataFrame:
    """Recorta o stream canônico para os eventos que treino e inferência consomem.

    Fidelidade a Shi et al. 2022 / TCC 1: o Code-DKT foi treinado sobre `Run.Program` apenas
    (`data_loader.filter_for_bkt_dkt`, o filtro por trás de `sequences_bkt_dkt.pkl`). Manter os
    `Compile.Error` aqui injeta eventos rotulados como erro cujo Java não compila — logo sem
    path nenhum — e afasta a aplicação do oráculo: no CSEDM real eles são 57,6% das linhas do
    A439, e treinar com eles derrubou o first-attempt AUC para 0,6959, fora da banda ±3pp.

    NÃO altera o DataFrame recebido: o canônico segue inteiro para a EDA, que precisa dos
    compile errors. O índice é reconstruído porque o que consome isto adiante itera por posição.
    """
    return df[df["EventType"] == RUN_EVENT].copy().reset_index(drop=True)
