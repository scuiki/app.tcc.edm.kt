"""Trava global de pipeline: a única porta para a linha pipeline_lock (MODEL-03, D-07/D-08).

Primeira trava persistente do projeto. A trava NÃO vive em memória (uma trava em processo
não sobrevive a restart nem é observável por consulta — Anti-Pattern RESEARCH): ela é a
linha id=1 de pipeline_lock (flag SQLite + status), adquirida por escrita condicional sob
BEGIN IMMEDIATE e liberada de forma garantida via context manager (release ao terminar E ao
falhar, SC3). Espelha set_global_seed como única porta de seeding: estado explícito,
contido e observável (seeding.py).
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone


def pid_alive(pid: int) -> bool:
    """True se o processo `pid` existe e é acessível (liveness probe via os.kill)."""
    # os.kill(pid, 0) não envia sinal: só sonda existência. ESRCH (ProcessLookupError) =
    # não existe; EPERM (PermissionError) = existe mas de outro dono (raro em instância
    # única, --workers 1) — ainda conta como vivo.
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def pipeline_busy(conn: sqlite3.Connection) -> bool:
    """Pré-check BARATO e NÃO-autoritativo: lê o dono sem adquirir (D-02/D-05).

    O acquire autoritativo é do subprocess, como 1º ato. Isto aqui só rejeita cedo o "ocupado
    óbvio" para dar uma mensagem melhor; se dois POSTs correrem, o segundo perde o acquire LÁ e
    marca o próprio job como failed. NUNCA tratar como o gate — o gate é o acquire.
    """
    row = conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()
    return row is not None and row["holder_pid"] is not None and pid_alive(row["holder_pid"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def reclaim_orphan_lock(conn: sqlite3.Connection) -> None:
    """No startup, libera qualquer trava remanescente (holder_pid → NULL). Idempotente.

    Instância única ⇒ nenhum pipeline pode estar legitimamente vivo logo após um restart,
    então qualquer trava presente é órfã (D-08). O critério é a ausência de vida do dono
    (PID morto), nunca a passagem do tempo desde a aquisição (rejeitado D-08 / Pitfall 6)."""
    conn.execute("BEGIN IMMEDIATE;")
    try:
        conn.execute(
            "UPDATE pipeline_lock SET holder_pid=NULL, operation=NULL, "
            "job_id=NULL, acquired_at=NULL WHERE id=1;"
        )
        conn.execute("COMMIT;")
    except BaseException:
        conn.execute("ROLLBACK;")
        raise


class PipelineLock:
    """Adquire/libera a trava global. Use `with lock.acquire(op, job_id):` (SC3).

    É a única porta para a linha pipeline_lock: acquire faz a escrita condicional atômica,
    release zera a linha, e o context manager garante release ao terminar E ao falhar.
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
        self._held = False

    def acquire(self, operation: str, job_id: int | None) -> "PipelineLock":
        """Toma a trava se livre ou se o dono atual está morto (stale). Atômico.

        Retorna self (truthy + context manager) quando toma a trava; um sentinela falsy
        quando há dono vivo ("pipeline busy"). BEGIN IMMEDIATE serializa o SELECT-then-UPDATE
        contra TOCTOU (Pitfall 4): pega o write-lock no início, não na 1ª escrita, fechando
        a janela em que outro escritor entraria entre a leitura e o UPDATE."""
        conn = self._conn
        conn.execute("BEGIN IMMEDIATE;")
        try:
            row = conn.execute(
                "SELECT holder_pid FROM pipeline_lock WHERE id=1;"
            ).fetchone()
            held = row is not None and row["holder_pid"] is not None
            if held and pid_alive(row["holder_pid"]):
                conn.execute("ROLLBACK;")  # ocupado por pipeline vivo — caller surfaces "busy"
                return _DENIED
            # livre OU dono morto (stale) → tomamos a trava
            conn.execute(
                "UPDATE pipeline_lock SET holder_pid=?, operation=?, job_id=?, "
                "acquired_at=? WHERE id=1;",
                (os.getpid(), operation, job_id, _now_iso()),
            )
            conn.execute("COMMIT;")
        except BaseException:
            conn.execute("ROLLBACK;")
            raise
        self._held = True
        return self

    def release(self) -> None:
        """Zera a linha da trava (holder_pid → NULL). Idempotente."""
        conn = self._conn
        conn.execute("BEGIN IMMEDIATE;")
        try:
            conn.execute(
                "UPDATE pipeline_lock SET holder_pid=NULL, operation=NULL, "
                "job_id=NULL, acquired_at=NULL WHERE id=1;"
            )
            conn.execute("COMMIT;")
        except BaseException:
            conn.execute("ROLLBACK;")
            raise
        self._held = False

    def __bool__(self) -> bool:
        return self._held

    def __enter__(self) -> "PipelineLock":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        # Release ao sair do `with` — inclusive sob exceção (SC3). Retorna False para
        # propagar qualquer exceção levantada dentro do bloco.
        if self._held:
            self.release()
        return False


class _Denied:
    """Sentinela falsy devolvido quando a trava está ocupada por um dono vivo.

    Serve de context manager no-op (caso o caller use `with`) e avalia falsy, então
    `if not lock.acquire(...)` detecta o "pipeline busy" sem exceção."""

    def __bool__(self) -> bool:
        return False

    def __enter__(self) -> "_Denied":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


_DENIED = _Denied()
