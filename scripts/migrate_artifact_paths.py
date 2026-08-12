"""Migração pontual dos artefatos gravados no layout antigo (999.1 / B5).

Antes: `<base>/<turma_id>/<assignment_id>/models/v<N>`, onde `<base>` já terminava em
`.../models` — daí o segmento duplicado. Agora: `<base>/<assignment_id>/v<N>`.

Idempotente: um artefato já no layout novo é ignorado. Move o diretório PRIMEIRO e só então
atualiza a linha; se o move falhar, o banco segue apontando para o que existe.

Uso (dentro do container): python -m scripts.migrate_artifact_paths [--apply]
Sem --apply só mostra o que faria.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path


def _new_dir(old: Path) -> Path | None:
    """`.../models/<turma>/<assignment>/models/v<N>` → `.../models/<assignment>/v<N>`."""
    parts = list(old.parts)
    if len(parts) < 5 or parts[-2] != "models":
        return None  # já migrado (ou formato desconhecido): não mexe
    version, assignment = parts[-1], parts[-3]
    return Path(*parts[:-4]) / assignment / version


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="app.db")
    parser.add_argument("--apply", action="store_true", help="sem isto, apenas simula")
    args = parser.parse_args(argv)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = list(conn.execute("SELECT id, artifact_dir FROM model_artifact ORDER BY id;"))

    planned = []
    for row in rows:
        old = Path(row["artifact_dir"])
        new = _new_dir(old)
        if new is None:
            print(f"  [ok]    artefato {row['id']}: já no layout novo ({old})")
            continue
        planned.append((row["id"], old, new))
        print(f"  [move]  artefato {row['id']}: {old} -> {new}")

    if not planned:
        print("Nada a migrar.")
        return 0
    if not args.apply:
        print("\nSimulação. Use --apply para executar.")
        return 0

    for artifact_id, old, new in planned:
        if not old.exists():
            print(f"  ! artefato {artifact_id}: origem inexistente, pulando ({old})")
            continue
        new.parent.mkdir(parents=True, exist_ok=True)
        old.rename(new)  # FS primeiro: se falhar, o banco segue apontando para o que existe
        conn.execute(
            "UPDATE model_artifact SET artifact_dir=? WHERE id=?;", (str(new), artifact_id)
        )
    conn.commit()

    # Limpa os diretórios-pai que ficaram vazios pelo move (o `<turma_id>/<assignment_id>/models`).
    for _artifact_id, old, _new in planned:
        for parent in list(old.parents)[:3]:
            try:
                parent.rmdir()
            except OSError:
                break  # não vazio: para de subir

    print(f"\n{len(planned)} artefato(s) migrado(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
