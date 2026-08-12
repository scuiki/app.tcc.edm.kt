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
    # 1ª aquisição: a trava está livre, deve tomar (handle avalia truthy).
    assert PipelineLock(conn).acquire("train", job_id=1)
    # holder_pid agora é este processo (vivo), então uma 2ª aquisição é negada.
    assert _holder_pid(conn) == os.getpid()
    assert not PipelineLock(conn).acquire("upload", job_id=2)


def test_busy_state_observable(tmp_db):
    conn = tmp_db
    assert PipelineLock(conn).acquire("train", job_id=7)
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
    assert PipelineLock(conn).acquire("upload", job_id=2)
    assert _holder_pid(conn) == os.getpid()


def test_startup_reclaims_orphan(tmp_db):
    conn = tmp_db
    # Trava de um dono MORTO — o que "órfã" quer dizer. Este teste antes usava os.getpid() (um
    # dono VIVO) e esperava a limpeza: fixava o bug, sob a premissa "instância única ⇒ nada pode
    # estar vivo no startup". O subprocess de treino não segue o ciclo de vida do web.
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation=?, job_id=? WHERE id=1;",
        (_dead_pid(), "train", 5),
    )
    reclaim_orphan_lock(conn)
    assert _holder_pid(conn) is None
    # Idempotente: reclamar de novo sobre trava já livre não quebra.
    reclaim_orphan_lock(conn)
    assert _holder_pid(conn) is None


# --- B3/B4: recuperar só o que está órfão de fato, liberar só o que é seu -------------


def test_reclaim_leaves_a_live_holder_alone(tmp_db):
    """O docstring de reclaim_orphan_lock sempre prometeu "critério = PID morto"; o código
    limpava incondicionalmente.

    Hoje isso é inofensivo por um acidente de deploy: o uvicorn é PID 1 no container, então
    reiniciar o container mata o subprocess de treino junto. Com --reload em desenvolvimento o
    acidente acaba — o uvicorn reinicia, o treino sobrevive, a trava é limpa, e um segundo
    treino entra na MESMA GPU de 6 GB.
    """
    conn = tmp_db
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', job_id=7 WHERE id=1;",
        (os.getpid(),),  # dono VIVO: este processo
    )

    reclaim_orphan_lock(conn)

    assert _holder_pid(conn) == os.getpid()  # intocado


def test_reclaim_frees_a_dead_holder(tmp_db):
    conn = tmp_db
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', job_id=7 WHERE id=1;",
        (_dead_pid(),),
    )

    reclaim_orphan_lock(conn)

    assert _holder_pid(conn) is None


def test_release_does_not_clear_a_lock_owned_by_someone_else(tmp_db):
    # Sem a guarda de posse, um release tardio zeraria a trava de OUTRO pipeline em andamento.
    conn = tmp_db
    alheio = _dead_pid()  # capturado UMA vez: _dead_pid() varre PIDs livres e não é determinístico
    lock = PipelineLock(conn)
    conn.execute(
        "UPDATE pipeline_lock SET holder_pid=?, operation='training', job_id=99 WHERE id=1;",
        (alheio,),
    )

    lock.release()  # este objeto nunca adquiriu nada

    assert _holder_pid(conn) == alheio
