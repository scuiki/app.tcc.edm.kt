# Proveniência (commit + hash do dado); o A439 já teve 2 versões com AUC diferente sem registro

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


def git_commit(repo_root: Path) -> str | None:
    # SHA do HEAD, ou None se não houver `.git` legível (imagem sem o repo montado).
    head = repo_root / ".git" / "HEAD"
    try:
        content = head.read_text().strip()
    except OSError:
        return None
    if not content.startswith("ref:"):
        return content  # HEAD destacado, já é o próprio SHA
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


def dataset_hash(events: pd.DataFrame) -> str:
    # SHA-256 do dado do treino, em CSV; é o conteúdo, não um arquivo (mesmo dado, mesmo hash)
    return hashlib.sha256(events.to_csv(index=False).encode()).hexdigest()
