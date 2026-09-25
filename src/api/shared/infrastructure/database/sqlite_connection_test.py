from __future__ import annotations

import threading

from api.shared.infrastructure.database.sqlite_connection import connect


def test_connection_opened_in_one_thread_works_in_another(tmp_path):
    # É o caminho de toda requisição, a dependência abre numa thread e a rota roda em outra
    conn = connect(str(tmp_path / "app.db"))
    errors: list[BaseException] = []

    def use_in_other_thread() -> None:
        try:
            conn.execute("CREATE TABLE t (x INTEGER)")
            conn.execute("INSERT INTO t VALUES (1)")
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=use_in_other_thread)
    worker.start()
    worker.join()

    assert errors == []
    assert conn.execute("SELECT x FROM t").fetchone()[0] == 1
    conn.close()
