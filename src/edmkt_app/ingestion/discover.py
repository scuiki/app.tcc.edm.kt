"""Estágio A da ingestão — descoberta de layout + extração sandbox do upload (D-01/02/03).

Fronteira de impureza entre o `.zip` arbitrário do professor e o núcleo puro. Toda função
aqui é read-only sobre o FS de upload OU escreve apenas sob um `dest` interno controlado; a
detecção NÃO adquire a trava do pipeline nem importa o núcleo científico (Lock Timing,
Pitfall 5): prendê-la aqui a manteria presa durante a escolha humana de variante (D-03).

`find_code_states`/`find_main_tables` substituem o `_SPLITS` hard-coded do TCC1 por glob
tolerante (D-02: CodeStates pode viver em CodeStates/ ou LinkTables/; D-03: N MainTable viram
variantes para o professor escolher, sem adivinhar). `extract_zip` espelha a defesa de
path-traversal de `values.ConfinedPath`.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from api.shared.infrastructure.confined_path import ConfinedPath

# Tetos conservadores contra zip-bomb (DoS — RESEARCH §Security): o limite exato é detalhe
# operacional; escolhidos folgados o bastante para um ProgSnap2 real (≈milhares de CodeStates),
# apertados o bastante para barrar um zip patológico antes de exaurir disco/inodes.
_MAX_MEMBERS = 20_000
_MAX_TOTAL_UNCOMPRESSED = 2 * 1024 * 1024 * 1024  # 2 GiB descomprimidos somados
_CHUNK = 1024 * 1024  # 1 MiB por leitura: limita a RAM por membro durante a descompressão


def find_code_states(root: Path) -> Path | None:
    candidates = (
        root / "CodeStates" / "CodeStates.csv",
        root / "LinkTables" / "CodeStates.csv",  # variante CodeWorkout de referência (D-02)
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
        # Pre-check barato: file_size vem do header (atacante-controlado), então só serve como
        # rejeição rápida de um zip honesto-mas-grande. NÃO é a defesa real — um bomb declara
        # headers minúsculos e passa aqui. O guarda autoritativo é o contador de bytes REAIS abaixo.
        total = sum(i.file_size for i in infos)
        if total > _MAX_TOTAL_UNCOMPRESSED:
            raise ValueError("zip excede o teto de tamanho descomprimido")

        written_total = 0
        for info in infos:
            # O nome do membro NÃO é caminho confiável: resolve sob base e valida ANTES de
            # escrever (mesma disciplina do _version_dir). Path absoluto ou ../ escapa => rejeita.
            try:
                resolved = Path(ConfinedPath(base / info.filename, root=base))
            except ValueError:
                # Mensagem própria, sem o caminho: o nome do membro pode carregar conteúdo do aluno.
                raise ValueError("path traversal detectado na extração do zip") from None
            if info.is_dir():
                resolved.mkdir(parents=True, exist_ok=True)
                continue
            resolved.parent.mkdir(parents=True, exist_ok=True)
            # Streaming em blocos contando bytes DESCOMPRIMIDOS reais: member.read() sem limite
            # descomprimiria o membro inteiro em RAM, então um bomb com header mentido derrubaria
            # o processo apesar do pre-check. Aborta no instante em que o real ultrapassa o teto.
            with zf.open(info) as member, open(resolved, "wb") as out:
                while True:
                    chunk = member.read(_CHUNK)
                    if not chunk:
                        break
                    written_total += len(chunk)
                    if written_total > _MAX_TOTAL_UNCOMPRESSED:
                        raise ValueError("zip excede o teto de tamanho descomprimido")
                    out.write(chunk)

    return base
