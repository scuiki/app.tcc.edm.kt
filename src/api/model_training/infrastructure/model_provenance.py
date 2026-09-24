"""A proveniência de um treino: qual código (commit) e qual dado (hash do Parquet) geraram a versão.

O banco chegou a guardar duas versões do A439 com AUC diferente (0,6959 e 0,7452) e nenhum registro
do que mudou entre elas. Duas colunas transformam a anedota em evidência auditável.

`git_commit` é lido do `.git` na mão, sem depender do binário `git` no container.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def git_commit(repo_root: Path) -> str | None:
    """SHA do HEAD, ou None se não houver `.git` legível (imagem sem o repo montado)."""
    head = repo_root / ".git" / "HEAD"
    try:
        content = head.read_text().strip()
    except OSError:
        return None
    if not content.startswith("ref:"):
        return content  # HEAD destacado: já é o próprio SHA
    ref = (repo_root / ".git" / content.split(" ", 1)[1].strip()).resolve()
    try:
        return ref.read_text().strip()
    except OSError:
        # Ref empacotada (packed-refs) em vez de arquivo solto.
        try:
            for line in (repo_root / ".git" / "packed-refs").read_text().splitlines():
                if line.endswith(content.split(" ", 1)[1].strip()):
                    return line.split(" ", 1)[0]
        except OSError:
            return None
    return None


def file_hash(path: Path) -> str | None:
    """SHA-256 do Parquet canônico que alimentou o treino — a identidade do DADO de entrada."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None
