# Fronteira entre zip arbitrário e o sistema; layout tolerante, N MainTable.csv viram opções.

from __future__ import annotations

import zipfile
from pathlib import Path

from api.classroom_import.domain.value_objects.detected_upload import DetectedUpload
from api.shared.infrastructure.filesystem import data_layout
from api.shared.infrastructure.filesystem.confined_path import ConfinedPath

# Tetos conservadores contra zip-bomb; folgados para ProgSnap2 real, apertados contra bomb.
_MAX_MEMBERS = 20_000
_MAX_TOTAL_UNCOMPRESSED = 2 * 1024 * 1024 * 1024  # 2 GiB descomprimidos somados
_CHUNK = 1024 * 1024  # 1 MiB por leitura, limita a RAM por membro durante a descompressão


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
    # Ordenado e só leitura, N caminhos são N opções para o professor; não se adivinha.
    return sorted(root.rglob("MainTable.csv"))


def extract_zip(zip_path: Path, dest: Path) -> Path:
    base = dest.resolve()
    base.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path) as zf:
        infos = zf.infolist()
        if len(infos) > _MAX_MEMBERS:
            # Sem despejar nomes de membros no erro (podem carregar conteúdo do aluno).
            raise ValueError(f"zip excede o teto de {_MAX_MEMBERS} membros")
        # Pre-check por file_size é barato mas não é a defesa real; o guarda é o contador abaixo.
        total = sum(i.file_size for i in infos)
        if total > _MAX_TOTAL_UNCOMPRESSED:
            raise ValueError("zip excede o teto de tamanho descomprimido")

        written_total = 0
        for info in infos:
            # O nome do membro não é caminho confiável; resolve sob base e valida antes de escrever.
            try:
                resolved = Path(ConfinedPath(base / info.filename, root=base))
            except ValueError:
                # Mensagem própria, sem o caminho, o nome do membro pode carregar conteúdo do aluno.
                raise ValueError("path traversal detectado na extração do zip") from None
            if info.is_dir():
                resolved.mkdir(parents=True, exist_ok=True)
                continue
            resolved.parent.mkdir(parents=True, exist_ok=True)
            # Streaming conta bytes reais descomprimidos; ler tudo de vez estouraria a RAM num bomb.
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


# IProgSnapUploadExtractor, extrai cada envio numa pasta própria em raw/ e lista o que encontrou.
class ProgSnapZipExtractor:
    def extract(self, zip_path: Path, classroom_id: int, upload_name: str) -> DetectedUpload:
        destination = data_layout.raw_upload_dir(classroom_id, upload_name)
        # Dois envios no mesmo segundo e com o mesmo nome não se misturam
        suffix = 2
        while destination.exists():
            destination = data_layout.raw_upload_dir(classroom_id, f"{upload_name}-{suffix}")
            suffix += 1
        raw_dir = extract_zip(Path(zip_path), destination)
        return DetectedUpload(
            raw_dir=raw_dir,
            main_tables=find_main_tables(raw_dir),
            code_snapshots=find_code_snapshots_file(raw_dir),
        )
