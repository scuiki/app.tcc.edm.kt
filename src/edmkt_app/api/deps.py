"""Dependências FastAPI — conexão por requisição + o composition root dos use cases.

Cada requisição abre a SUA conexão via `connect(db_path)` e a fecha no fim (Pitfall 2): o web e
o subprocess de treino NUNCA compartilham um objeto Python; a coordenação é só pela linha
`pipeline_lock` + WAL.

As factories abaixo são o **composition root**: o único lugar que decide qual use case recebe
qual infraestrutura. Como a conexão é por-requisição, o use case também nasce por-requisição —
o FastAPI resolve a cadeia `get_conn → factory → rota` sozinho.

Por que o use case recebe `conn` e não repositórios prontos: os repositórios aqui são casca
fina sobre a conexão, e a suíte já troca infraestrutura passando um SQLite real (fixture
`tmp_db`), não mocks de repositório. Injetá-los seria cerimônia por uma flexibilidade que
nenhum teste usa.
"""

from __future__ import annotations

import sqlite3
from typing import Iterator

from fastapi import Depends, Request

from api.shared.infrastructure.database.sqlite_connection import connect
from edmkt_app.use_cases.get_eda import GetEdaUseCase
from edmkt_app.use_cases.get_mastery import GetMasteryUseCase
from edmkt_app.use_cases.get_recommendations import GetRecommendationsUseCase
from edmkt_app.use_cases.get_training_history import GetTrainingHistoryUseCase
from edmkt_app.use_cases.get_training_status import GetTrainingStatusUseCase
from edmkt_app.use_cases.start_training import StartTrainingUseCase


def get_conn(request: Request) -> Iterator[sqlite3.Connection]:
    conn = connect(request.app.state.db_path)
    try:
        yield conn
    finally:
        conn.close()


# --- escrita ---------------------------------------------------------------------


def start_training_uc(conn: sqlite3.Connection = Depends(get_conn)) -> StartTrainingUseCase:
    return StartTrainingUseCase(conn)


# --- leitura (não estendem a base de escrita) -------------------------------------


def get_mastery_uc(conn: sqlite3.Connection = Depends(get_conn)) -> GetMasteryUseCase:
    return GetMasteryUseCase(conn)


def get_eda_uc(conn: sqlite3.Connection = Depends(get_conn)) -> GetEdaUseCase:
    return GetEdaUseCase(conn)


def get_recommendations_uc(
    conn: sqlite3.Connection = Depends(get_conn),
) -> GetRecommendationsUseCase:
    return GetRecommendationsUseCase(conn)


def get_training_status_uc(
    conn: sqlite3.Connection = Depends(get_conn),
) -> GetTrainingStatusUseCase:
    return GetTrainingStatusUseCase(conn)


def get_training_history_uc(
    conn: sqlite3.Connection = Depends(get_conn),
) -> GetTrainingHistoryUseCase:
    return GetTrainingHistoryUseCase(conn)
