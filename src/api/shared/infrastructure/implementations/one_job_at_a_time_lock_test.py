# Trava global de pipeline por flag SQLite com PID-liveness, estado observável por SELECT.
from __future__ import annotations

import os

import pytest

from api.shared.infrastructure.implementations.one_job_at_a_time_lock import (
    OneJobAtATimeLock,
    is_process_alive,
    release_lock_of_dead_holder,
)
from tests.fixtures.job_lock import lock_holder_pid


# Um PID garantidamente morto, fork+exit e o wait() libera o número para os.kill levantar ESRCH.
def _dead_pid() -> int:
    pid = os.fork()
    if pid == 0:  # filho, sai imediatamente
        os._exit(0)
    os.waitpid(pid, 0)
    return pid


def test_pid_alive():
    assert is_process_alive(os.getpid()) is True
    assert is_process_alive(_dead_pid()) is False
    assert is_process_alive(0) is False
    assert is_process_alive(-1) is False


def test_acquire_blocks_when_held(tmp_db):
    conn = tmp_db
    # 1ª aquisição, a trava está livre e deve tomar (handle avalia truthy).
    assert OneJobAtATimeLock(conn).acquire("train", job_id=1)
    # holder_pid agora é este processo (vivo), então uma 2ª aquisição é negada.
    assert lock_holder_pid(conn) == os.getpid()
    assert not OneJobAtATimeLock(conn).acquire("upload", job_id=2)


def test_busy_state_observable(tmp_db):
    conn = tmp_db
    assert OneJobAtATimeLock(conn).acquire("train", job_id=7)
    # Estado bloqueado é visível por SELECT, holder_pid não-nulo mais operation gravada.
    row = conn.execute(
        "SELECT holder_pid, operation, job_id FROM pipeline_lock WHERE id=1;"
    ).fetchone()
    assert row["holder_pid"] is not None
    assert row["operation"] == "train"
    assert row["job_id"] == 7


def test_release_on_finish(tmp_db):
    conn = tmp_db
    with OneJobAtATimeLock(conn).acquire("train", job_id=1):
        assert lock_holder_pid(conn) == os.getpid()
    # Ao sair normalmente do with, a linha volta a holder_pid NULL.
    assert lock_holder_pid(conn) is None


def test_release_on_failure(tmp_db):
    conn = tmp_db
    with pytest.raises(RuntimeError):
        with OneJobAtATimeLock(conn).acquire("train", job_id=1):
            assert lock_holder_pid(conn) == os.getpid()
            raise RuntimeError("falha no meio da operação")
    # A trava é liberada mesmo com exceção (release no __exit__); exceção propaga.
    assert lock_holder_pid(conn) is None


def test_acquire_steals_dead_holder(tmp_db):
    conn = tmp_db
    dead = _dead_pid()
    # Simula um dono morto, grava holder_pid de um PID que não existe mais.
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation=?, job_id=? WHERE id=1;",
        (dead, "train", 99),
    )
    # Dono morto = trava stale; acquire consegue tomar.
    assert OneJobAtATimeLock(conn).acquire("upload", job_id=2)
    assert lock_holder_pid(conn) == os.getpid()


# Trava de um dono MORTO, o subprocess de treino não segue o ciclo de vida do web.
def test_startup_reclaims_orphan(tmp_db):
    conn = tmp_db
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation=?, job_id=? WHERE id=1;",
        (_dead_pid(), "train", 5),
    )
    release_lock_of_dead_holder(conn)
    assert lock_holder_pid(conn) is None
    # Idempotente, reclamar de novo sobre trava já livre não quebra.
    release_lock_of_dead_holder(conn)
    assert lock_holder_pid(conn) is None


# Recuperar só o que está órfão de fato, e liberar só o que é seu.


# Com --reload em dev o web reinicia sozinho e um treino vivo perderia a trava para outro job.
def test_reclaim_leaves_a_live_holder_alone(tmp_db):
    conn = tmp_db
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', job_id=7 WHERE id=1;",
        (os.getpid(),),  # dono VIVO, este processo
    )

    release_lock_of_dead_holder(conn)

    assert lock_holder_pid(conn) == os.getpid()  # intocado


def test_reclaim_frees_a_dead_holder(tmp_db):
    conn = tmp_db
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', job_id=7 WHERE id=1;",
        (_dead_pid(),),
    )

    release_lock_of_dead_holder(conn)

    assert lock_holder_pid(conn) is None


def test_release_does_not_clear_a_lock_owned_by_someone_else(tmp_db):
    # Sem a guarda de posse, um release tardio zeraria a trava de OUTRO pipeline em andamento.
    conn = tmp_db
    alheio = _dead_pid()  # capturado UMA vez, _dead_pid() varre PIDs livres e não é determinístico
    lock = OneJobAtATimeLock(conn)
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', job_id=99 WHERE id=1;",
        (alheio,),
    )

    lock.release()  # este objeto nunca adquiriu nada

    assert lock_holder_pid(conn) == alheio
