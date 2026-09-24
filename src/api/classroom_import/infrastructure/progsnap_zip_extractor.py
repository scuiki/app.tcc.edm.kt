"""Abre o .zip do professor num diretório controlado e encontra as tabelas do ProgSnap2.

Fronteira entre um zip arbitrário e o resto do sistema: tudo aqui só lê o upload ou escreve sob
um destino interno. A detecção NÃO pega a trava de job: prendê-la aqui a manteria presa enquanto o
professor escolhe qual MainTable importar.

O layout é tolerante: o CodeStates.csv pode morar em CodeStates/ ou LinkTables/, e N MainTable.csv
viram opções para o professor escolher, sem adivinhar.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

from api.assignments.domain.classroom_slug import ClassroomSlug
from api.classroom_import.domain.progsnap_upload import DetectedUpload
from api.shared.infrastructure import data_layout
from api.shared.infrastructure.confined_path import ConfinedPath

# Tetos conservadores contra zip-bomb (DoS): o limite exato é detalhe
# operacional; escolhidos folgados o bastante para um ProgSnap2 real (≈milhares de CodeStates),
# apertados o bastante para barrar um zip patológico antes de exaurir disco/inodes.
_MAX_MEMBERS = 20_000
_MAX_TOTAL_UNCOMPRESSED = 2 * 1024 * 1024 * 1024  # 2 GiB descomprimidos somados
_CHUNK = 1024 * 1024  # 1 MiB por leitura: limita a RAM por membro durante a descompressão


def find_code_snapshots_file(root: Path) -> Path | None:
    candidates = (
        root / "CodeStates" / "CodeStates.csv",
        root / "LinkTables" / "CodeStates.csv",  # a variante CodeWorkout de referência
        *sorted(root.rglob("CodeStates.csv")),  # fallback tolerante, ordem estável
    )
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def find_main_tables(root: Path) -> list[Path]:
    # Ordenado e só leitura: N caminhos são N opções para o professor; aqui não se adivinha.
    return sorted(root.rglob("MainTable.csv"))


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
            # escrever. Caminho absoluto ou ../ que escapa é recusado.
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


class ProgSnapZipExtractor:
    """ProgSnapUploadExtractor: extrai em data/<turma>/raw/ e lista o que encontrou."""

    def extract(self, zip_path: Path, classroom_slug: ClassroomSlug) -> DetectedUpload:
        raw_dir = extract_zip(Path(zip_path), data_layout.raw_upload_dir(classroom_slug))
        return DetectedUpload(
            raw_dir=raw_dir,
            main_tables=find_main_tables(raw_dir),
            code_snapshots=find_code_snapshots_file(raw_dir),
        )
