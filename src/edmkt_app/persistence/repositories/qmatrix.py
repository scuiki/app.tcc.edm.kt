"""Q-matrix: os bindings problema↔KC e as consultas que a guarda 0-KC usa (D-07)."""

from __future__ import annotations

import sqlite3
from typing import Optional

from edmkt_app.persistence import models


class QMatrixRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def insert(self, qmatrix: models.QMatrix) -> int:
        cur = self._conn.execute(
            "INSERT INTO qmatrix (assignment_id, kc_id, problem_id) VALUES (?, ?, ?);",
            (qmatrix.assignment_id, qmatrix.kc_id, qmatrix.problem_id),
        )
        return cur.lastrowid

    def get(self, qmatrix_id: int) -> Optional[models.QMatrix]:
        row = self._conn.execute(
            "SELECT id, assignment_id, kc_id, problem_id FROM qmatrix WHERE id = ?;",
            (qmatrix_id,),
        ).fetchone()
        if row is None:
            return None
        return models.QMatrix(
            id=row["id"],
            assignment_id=row["assignment_id"],
            kc_id=row["kc_id"],
            problem_id=row["problem_id"],
        )

    def list_by_assignment(self, assignment_id: int) -> list[models.QMatrix]:
        rows = self._conn.execute(
            "SELECT id, assignment_id, kc_id, problem_id FROM qmatrix WHERE assignment_id = ?;",
            (assignment_id,),
        ).fetchall()
        return [
            models.QMatrix(
                id=r["id"],
                assignment_id=r["assignment_id"],
                kc_id=r["kc_id"],
                problem_id=r["problem_id"],
            )
            for r in rows
        ]

    def list_by_problem(self, assignment_id: int, problem_id: int) -> list[models.QMatrix]:
        rows = self._conn.execute(
            "SELECT id, assignment_id, kc_id, problem_id FROM qmatrix "
            "WHERE assignment_id = ? AND problem_id = ?;",
            (assignment_id, problem_id),
        ).fetchall()
        return [
            models.QMatrix(
                id=r["id"],
                assignment_id=r["assignment_id"],
                kc_id=r["kc_id"],
                problem_id=r["problem_id"],
            )
            for r in rows
        ]

    def insert_bindings(
        self, assignment_id: int, kc_id: int, problem_ids: list[int]
    ) -> None:
        # Bulk-insert no shape de _persist_atomic: loop de insert dentro da txn do caller
        # (não abre txn própria). OR IGNORE evita duplicar o par (problem, kc) já ligado.
        for problem_id in problem_ids:
            self._conn.execute(
                "INSERT OR IGNORE INTO qmatrix (assignment_id, kc_id, problem_id) "
                "VALUES (?, ?, ?);",
                (assignment_id, kc_id, problem_id),
            )

    def repoint_bindings(self, assignment_id: int, kc_keep: int, kc_drop: int) -> None:
        # merge = união de bindings: cada linha de kc_drop vira binding de kc_keep
        # (UPDATE OR IGNORE descarta o par (problem, kc_keep) que já existe), depois somem as
        # linhas de kc_drop. Sem abrir txn — roda dentro do `with transaction` do caller.
        self._conn.execute(
            "UPDATE OR IGNORE qmatrix SET kc_id = ? WHERE kc_id = ? AND assignment_id = ?;",
            (kc_keep, kc_drop, assignment_id),
        )
        self._conn.execute(
            "DELETE FROM qmatrix WHERE kc_id = ? AND assignment_id = ?;",
            (kc_drop, assignment_id),
        )

    def delete_by_kc(self, kc_id: int) -> None:
        self._conn.execute("DELETE FROM qmatrix WHERE kc_id = ?;", (kc_id,))

    def problems_of_kc(self, kc_id: int) -> list[int]:
        # Os problemas que ESTE KC liga — colhidos ANTES de remover/mesclar para sabermos quais
        # checar contra a invariante 0-KC depois (D-07): só esses problemas podem zerar.
        rows = self._conn.execute(
            "SELECT DISTINCT problem_id FROM qmatrix WHERE kc_id = ? AND problem_id IS NOT NULL;",
            (kc_id,),
        ).fetchall()
        return [r["problem_id"] for r in rows]

    def kc_count_for_problem(self, assignment_id: int, problem_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS n FROM qmatrix WHERE assignment_id = ? AND problem_id = ?;",
            (assignment_id, problem_id),
        ).fetchone()
        return row["n"]
