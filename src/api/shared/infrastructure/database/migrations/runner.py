# Runner forward-only sobre PRAGMA user_version, cada DDL e o bump correm na mesma transação.
from __future__ import annotations

import pathlib
import sqlite3
from typing import Optional

from api.shared.infrastructure.database.sqlite_connection import transaction


def _default_migrations_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent


# Varre a linha alternando in_string a cada aspa simples, um `--` dentro de string é preservado.
def _strip_line_comment(line: str) -> str:
    in_string = False
    i = 0
    while i < len(line):
        c = line[i]
        if c == "'":
            in_string = not in_string
        elif c == "-" and not in_string and i + 1 < len(line) and line[i + 1] == "-":
            return line[:i]
        i += 1
    return line


# executescript() dá um COMMIT implícito ao entrar, o que quebraria o DDL+bump atômico.
def _split_statements(sql: str) -> list[str]:
    # Remove o comentário `--` inline antes do split, senão um `;` dentro dele gruda statements.
    no_comments = "\n".join(_strip_line_comment(ln) for ln in sql.splitlines())
    return [stmt.strip() for stmt in no_comments.split(";") if stmt.strip()]


def run_migrations(conn: sqlite3.Connection, migrations_dir: Optional[pathlib.Path] = None) -> None:
    migrations_dir = pathlib.Path(migrations_dir) if migrations_dir else _default_migrations_dir()
    current = conn.execute("PRAGMA user_version;").fetchone()[0]
    scripts = sorted(migrations_dir.glob("[0-9][0-9][0-9][0-9]_*.sql"))
    for script in scripts:
        version = int(script.name[:4])
        if version <= current:
            continue
        with transaction(conn):
            for stmt in _split_statements(script.read_text()):
                conn.execute(stmt)
            # `version` vem do nome do arquivo (interno), exceção controlada a nunca interpolar SQL.
            conn.execute(f"PRAGMA user_version = {version};")
