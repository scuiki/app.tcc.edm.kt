# IQMatrixRepository sobre SQLite. Nenhum método abre transação, roda na IUnitOfWork de quem chama.

from __future__ import annotations

import sqlite3

from api.knowledge_components.domain.entities.qmatrix_binding_entity import QMatrixBinding


def _to_entity(row: sqlite3.Row) -> QMatrixBinding:
    return QMatrixBinding(
        id=row["id"],
        assignment_id=row["assignment_id"],
        kc_id=row["kc_id"],
        problem_id=row["problem_id"],
    )


class SqliteQMatrixRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, binding: QMatrixBinding) -> int:
        cur = self._conn.execute(
            "INSERT INTO qmatrix (assignment_id, kc_id, problem_id) VALUES (?, ?, ?);",
            (binding.assignment_id, binding.kc_id, binding.problem_id),
        )
        return cur.lastrowid

    def list_by_assignment(self, assignment_id: int) -> list[QMatrixBinding]:
        rows = self._conn.execute(
            "SELECT id, assignment_id, kc_id, problem_id FROM qmatrix WHERE assignment_id = ?;",
            (assignment_id,),
        ).fetchall()
        return [_to_entity(r) for r in rows]

    def bind_problems(self, assignment_id: int, kc_id: int, problem_ids: list[int]) -> None:
        # OR IGNORE, o UNIQUE (assignment, kc, problema) da 0006 descarta vínculo já existente.
        for problem_id in problem_ids:
            self._conn.execute(
                "INSERT OR IGNORE INTO qmatrix (assignment_id, kc_id, problem_id) "
                "VALUES (?, ?, ?);",
                (assignment_id, kc_id, problem_id),
            )

    def move_bindings(self, assignment_id: int, from_kc_id: int, to_kc_id: int) -> None:
        # União, cada vínculo de from_kc vira de to_kc, UPDATE OR IGNORE descarta o par repetido.
        self._conn.execute(
            "UPDATE OR IGNORE qmatrix SET kc_id = ? WHERE kc_id = ? AND assignment_id = ?;",
            (to_kc_id, from_kc_id, assignment_id),
        )
        self._conn.execute(
            "DELETE FROM qmatrix WHERE kc_id = ? AND assignment_id = ?;",
            (from_kc_id, assignment_id),
        )

    def delete_bindings_of(self, kc_id: int) -> None:
        self._conn.execute("DELETE FROM qmatrix WHERE kc_id = ?;", (kc_id,))

    def problems_of(self, kc_id: int) -> list[int]:
        rows = self._conn.execute(
            "SELECT DISTINCT problem_id FROM qmatrix WHERE kc_id = ? AND problem_id IS NOT NULL;",
            (kc_id,),
        ).fetchall()
        return [r["problem_id"] for r in rows]

    def count_kcs_of_problem(self, assignment_id: int, problem_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM qmatrix WHERE assignment_id = ? AND problem_id = ?;",
            (assignment_id, problem_id),
        ).fetchone()
        return row["n"]
