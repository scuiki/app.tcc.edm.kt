"""Trava global de pipeline por flag SQLite com PID-liveness (MODEL-03 / SC2 / SC3).

SC2: o estado bloqueado é observável por SELECT na linha pipeline_lock (não por variável
em memória). SC3: a trava é flag SQLite e libera ao terminar E ao falhar (release no
__exit__ do context manager). D-08: reclaim por PID morto, sem TTL. As asserções pinam
invariantes (acquire bloqueia 2ª aquisição viva, estado observável, release garantido,
reclaim libera órfã), não valores mágicos — espelha test_seeding.py. Herméticos, CPU-only,
sobre a fixture tmp_db de 02-01 (schema em user_version=1).
"""

from __future__ import annotations

import os

import pytest

from edmkt_app.persistence.lock import PipelineLock, pid_alive, reclaim_orphan_lock


def _dead_pid() -> int:
    """Um PID garantidamente morto: fork+exit e reusa o número já colhido (wait).

    Após o wait() o número de PID está livre (ainda não reciclado neste instante de
    teste), então os.kill(pid, 0) levanta ESRCH — exatamente o caso de dono stale."""
    pid = os.fork()
    if pid == 0:  # filho: sai imediatamente
        os._exit(0)
    os.waitpid(pid, 0)
    return pid


def _holder_pid(conn) -> int | None:
    """Lê o estado observável da trava por SELECT (SC2), não por atributo do objeto."""
    row = conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()
    return row["holder_pid"]


def test_pid_alive():
    assert pid_alive(os.getpid()) is True
    assert pid_alive(_dead_pid()) is False
    assert pid_alive(0) is False
    assert pid_alive(-1) is False


def test_acquire_blocks_when_held(tmp_db):
    conn = tmp_db
    # 1ª aquisição: a trava está livre, deve tomar.
    assert PipelineLock(conn).acquire("train", job_id=1) is True
    # holder_pid agora é este processo (vivo), então uma 2ª aquisição é negada.
    assert _holder_pid(conn) == os.getpid()
    assert PipelineLock(conn).acquire("upload", job_id=2) is False


def test_busy_state_observable(tmp_db):
    conn = tmp_db
    assert PipelineLock(conn).acquire("train", job_id=7) is True
    # Estado bloqueado é visível por SELECT: holder_pid não-nulo + operation gravada.
    row = conn.execute(
        "SELECT holder_pid, operation, job_id FROM pipeline_lock WHERE id=1;"
    ).fetchone()
    assert row["holder_pid"] is not None
    assert row["operation"] == "train"
    assert row["job_id"] == 7


def test_release_on_finish(tmp_db):
    conn = tmp_db
    with PipelineLock(conn).acquire("train", job_id=1):
        assert _holder_pid(conn) == os.getpid()
    # Ao sair normalmente do with, a linha volta a holder_pid NULL.
    assert _holder_pid(conn) is None


def test_release_on_failure(tmp_db):
    conn = tmp_db
    with pytest.raises(RuntimeError):
        with PipelineLock(conn).acquire("train", job_id=1):
            assert _holder_pid(conn) == os.getpid()
            raise RuntimeError("falha no meio da operação")
    # A trava é liberada mesmo com exceção (release no __exit__); exceção propaga.
    assert _holder_pid(conn) is None


def test_acquire_steals_dead_holder(tmp_db):
    conn = tmp_db
    dead = _dead_pid()
    # Simula um dono morto: grava holder_pid de um PID que não existe mais.
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation=?, job_id=? WHERE id=1;",
        (dead, "train", 99),
    )
    # Dono morto = trava stale; acquire consegue tomar.
    assert PipelineLock(conn).acquire("upload", job_id=2) is True
    assert _holder_pid(conn) == os.getpid()


def test_startup_reclaims_orphan(tmp_db):
    conn = tmp_db
    # Trava tomada (holder_pid qualquer — aqui um PID vivo: este processo).
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation=?, job_id=? WHERE id=1;",
        (os.getpid(), "train", 5),
    )
    # No startup, instância única ⇒ nada pode estar vivo: reclaim libera a órfã.
    reclaim_orphan_lock(conn)
    assert _holder_pid(conn) is None
    # Idempotente: reclamar de novo sobre trava já livre não quebra.
    reclaim_orphan_lock(conn)
    assert _holder_pid(conn) is None
