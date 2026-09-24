"""Numeração monótona de versão e o flip do ponteiro `published_model_id`.

Separados do store porque são operações sobre o BANCO, não sobre o blob: `next_version_number`
decide o próximo N e `flip_current` publica a versão. O flip é o ÚLTIMO passo da ordem
load-bearing blob→INSERT→flip (Pitfall 2) — publicar antes exporia um artefato incompleto.
"""

from __future__ import annotations

import sqlite3

from api.shared.infrastructure.database.sqlite_connection import transaction
from api.assignments.infrastructure.sqlite_assignment_repository import SqliteAssignmentRepository



def next_version_number(conn: sqlite3.Connection, assignment_id: int) -> int:
    """Próxima versão = MAX(version_number)+1 dentro do escopo (assignment). Pattern 2.

    Deve rodar na MESMA transação do INSERT do artefato (Pitfall 5), senão dois inserts
    concorrentes calculam o mesmo número; UNIQUE(assignment_id, version_number) é a rede."""
    row = conn.execute(
        "SELECT COALESCE(MAX(version_number), 0) + 1 AS next FROM model_artifact "
        "WHERE assignment_id = ?;",
        (assignment_id,),
    ).fetchone()
    return int(row["next"])


def flip_current(conn: sqlite3.Connection, assignment_id: int, new_version_id: int) -> None:
    """Troca Assignment.published_model_id por um UPDATE atômico (Pattern 5 / D-06).

    O flip é o ÚLTIMO passo da ordem load-bearing (blob write-once → INSERT → flip): só
    aqui um leitor passa a enxergar a nova versão, e sempre uma já completa (Pitfall 2). O
    ponteiro no DB é a fonte única — este UPDATE nunca toca o diretório do artefato."""
    with transaction(conn):
        SqliteAssignmentRepository(conn).set_published_model(assignment_id, new_version_id)
