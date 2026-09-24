# Trava global de pipeline, a linha pipeline_lock (nunca em memória), liberada mesmo sob falha.
from __future__ import annotations

import os
import sqlite3

from api.shared.infrastructure.database.sqlite_connection import transaction
from api.shared.application.services.clock import utc_now_iso


# os.kill(pid, 0) só sonda existência, sem enviar sinal; ESRCH é morto, EPERM ainda conta vivo.
def is_process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


# Pré-check barato e não autoritativo, o gate real é o acquire do subprocess como 1º ato.
def is_another_job_running(conn: sqlite3.Connection) -> bool:
    row = conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()
    return row is not None and row["holder_pid"] is not None and is_process_alive(row["holder_pid"])


# Critério é o PID do dono estar morto, nunca o tempo passado nem "reiniciou, logo é órfã".
def release_lock_of_dead_holder(conn: sqlite3.Connection) -> None:
    with transaction(conn):
        row = conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()
        holder = None if row is None else row["holder_pid"]
        if holder is not None and is_process_alive(holder):
            return  # dono vivo, a trava é legítima, não órfã
        conn.execute(
            "UPDATE pipeline_lock SET holder_pid=NULL, operation=NULL, "
            "job_id=NULL, acquired_at=NULL WHERE id=1;"
        )


class OneJobAtATimeLock:
    # Única porta para a linha pipeline_lock, use `with lock.acquire(op, job_id):`.
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._held = False

    def is_another_job_running(self) -> bool:
        return is_another_job_running(self._conn)

    # BEGIN IMMEDIATE pega o write-lock no início, serializando o select-then-update.
    def acquire(self, operation: str, job_id: int | None) -> "OneJobAtATimeLock":
        conn = self._conn
        with transaction(conn):
            row = conn.execute(
                "SELECT holder_pid FROM pipeline_lock WHERE id=1;"
            ).fetchone()
            held = row is not None and row["holder_pid"] is not None
            if held and is_process_alive(row["holder_pid"]):
                return _LOCK_DENIED  # ocupado por pipeline vivo, o caller reporta "busy"
            # livre OU dono morto (stale) -> tomamos a trava
            conn.execute(
                "UPDATE pipeline_lock SET holder_pid=?, operation=?, job_id=?, "
                "acquired_at=? WHERE id=1;",
                (os.getpid(), operation, job_id, utc_now_iso()),
            )
        self._held = True
        return self

    # WHERE holder_pid=? é a guarda de posse, sem ela um release tardio zeraria outra trava.
    def release(self) -> None:
        with transaction(self._conn):
            self._conn.execute(
                "UPDATE pipeline_lock SET holder_pid=NULL, operation=NULL, "
                "job_id=NULL, acquired_at=NULL WHERE id=1 AND holder_pid=?;",
                (os.getpid(),),
            )
        self._held = False

    def __bool__(self) -> bool:
        return self._held

    def __enter__(self) -> "OneJobAtATimeLock":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Release ao sair do `with`, inclusive sob exceção; False propaga a exceção do bloco.
        if self._held:
            self.release()
        return False


# Sentinela falsy quando a trava está ocupada por um dono vivo, e context manager no-op.
class _Denied:
    def __bool__(self) -> bool:
        return False

    def __enter__(self) -> "_Denied":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


_LOCK_DENIED = _Denied()
