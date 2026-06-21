"""Estágio A da ingestão — descoberta de layout + extração sandbox do upload (D-01/02/03).

Fronteira de impureza entre o `.zip` arbitrário do professor e o núcleo puro. Toda função
aqui é read-only sobre o FS de upload OU escreve apenas sob um `dest` interno controlado; a
detecção NÃO adquire a trava do pipeline nem importa o núcleo científico (Lock Timing,
Pitfall 5): prendê-la aqui a manteria presa durante a escolha humana de variante (D-03).

`find_code_states`/`find_main_tables` substituem o `_SPLITS` hard-coded do TCC1 por glob
tolerante (D-02: CodeStates pode viver em CodeStates/ ou LinkTables/; D-03: N MainTable viram
variantes para o professor escolher, sem adivinhar). `extract_zip` espelha a defesa de
path-traversal do `persistence/artifacts._version_dir`.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

# Tetos conservadores contra zip-bomb (DoS — RESEARCH §Security): o limite exato é detalhe
# operacional; escolhidos folgados o bastante para um ProgSnap2 real (≈milhares de CodeStates),
# apertados o bastante para barrar um zip patológico antes de exaurir disco/inodes.
_MAX_MEMBERS = 20_000
_MAX_TOTAL_UNCOMPRESSED = 2 * 1024 * 1024 * 1024  # 2 GiB descomprimidos somados


def find_code_states(root: Path) -> Path | None:
    candidates = (
        root / "CodeStates" / "CodeStates.csv",
        root / "LinkTables" / "CodeStates.csv",  # variante CodeWorkout/golden (D-02)
        *sorted(root.rglob("CodeStates.csv")),  # fallback tolerante, ordem estável
    )
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def find_main_tables(root: Path) -> list[Path]:
    # Ordenado e read-only: N caminhos => o professor escolhe (D-03); discover não adivinha.
    return sorted(root.rglob("MainTable.csv"))


def detect_variants(root: Path) -> dict:
    # Insumo do fluxo detectar→escolher→processar (D-03); a orquestração FastAPI vive no plano 05.
    return {
        "main_tables": find_main_tables(root),
        "code_states": find_code_states(root),
    }


def extract_zip(zip_path: Path, dest: Path) -> Path:
    base = dest.resolve()
    base.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        if len(infos) > _MAX_MEMBERS:
            # Sem despejar nomes de membros no erro (podem carregar conteúdo do aluno).
            raise ValueError(f"zip excede o teto de {_MAX_MEMBERS} membros")
        total = sum(i.file_size for i in infos)
        if total > _MAX_TOTAL_UNCOMPRESSED:
            raise ValueError("zip excede o teto de tamanho descomprimido")

        for info in infos:
            # O nome do membro NÃO é caminho confiável: resolve sob base e valida ANTES de
            # escrever (mesma disciplina do _version_dir). Path absoluto ou ../ escapa => rejeita.
            resolved = (base / info.filename).resolve()
            if base not in resolved.parents and resolved != base:
                raise ValueError("path traversal detectado na extração do zip")
            if info.is_dir():
                resolved.mkdir(parents=True, exist_ok=True)
                continue
            resolved.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as member, open(resolved, "wb") as out:
                out.write(member.read())

    return base
