"""Router de ingestão — reexpõe o `service` da Fase 3 por HTTP (D-12, fluxo D-03).

Só marshalla HTTP↔serviço: `POST /ingest` recebe o `.zip` multipart, salva e chama
`service.detect_variants`; `POST /ingest/process` chama `service.ingest` para a variante
escolhida. O serviço continua dono da trava, do commit atômico do Parquet e do rollback —
o router NÃO reimplementa nada disso nem re-extrai o zip (zip-slip/bomb já mitigados na
Fase 3 `discover.extract_zip`).
"""

from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from edmkt_app.api.deps import get_conn
from edmkt_app.ingestion import service

router = APIRouter(tags=["ingestion"])

# Teto de bytes do upload (DoS — T-04-UPLOAD): detalhe operacional deferido (D-12), não uma
# capacidade nova. Folgado para um ProgSnap2 real, apertado o bastante para barrar abuso antes
# de exaurir disco. O zip-bomb DESCOMPRIMIDO já tem teto próprio em discover.extract_zip.
_MAX_UPLOAD_BYTES = 512 * 1024 * 1024  # 512 MiB
_UPLOAD_CHUNK = 1024 * 1024


class ProcessRequest(BaseModel):
    turma_name: str
    raw_dir: str
    main_table: str


def _confine(p: Path, root: Path) -> Path:
    # Resolve-depois-confere: opera no path JÁ resolvido (fecha ../ e symlink) e exige que ele
    # seja root ou esteja sob ela. Espelha ArtifactStore._version_dir / _safe_csid_name.
    resolved_root = root.resolve()
    resolved_p = p.resolve()
    if not resolved_p.is_relative_to(resolved_root):
        raise HTTPException(status_code=400, detail="caminho fora da raiz de dados")
    return resolved_p


def _save_upload(upload: UploadFile, dest: Path) -> None:
    # Streaming em blocos contando bytes reais: ler o arquivo inteiro em RAM derrubaria o
    # processo num upload grande; aborta no instante em que o real ultrapassa o teto.
    written = 0
    with open(dest, "wb") as out:
        while True:
            chunk = upload.file.read(_UPLOAD_CHUNK)
            if not chunk:
                break
            written += len(chunk)
            if written > _MAX_UPLOAD_BYTES:
                out.close()
                dest.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="upload excede o teto de tamanho")
            out.write(chunk)


@router.post("/ingest", status_code=200)
def upload_and_detect(
    turma: str = Form(...),
    file: UploadFile = File(...),
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    """Recebe o `.zip`, extrai sob data/<slug>/raw/ e devolve as variantes de layout (D-03).

    READ-ONLY do estado compartilhado: detect_variants não toca a trava (Lock Timing).
    """
    slug = service._slug(turma)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        _save_upload(file, tmp_path)
        variants = service.detect_variants(tmp_path, slug)
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "turma_slug": slug,
        "raw_dir": str(variants["raw_dir"]),
        "main_tables": [str(p) for p in variants["main_tables"]],
        "code_states": str(variants["code_states"]) if variants["code_states"] else None,
    }


@router.post("/ingest/process", status_code=200)
def process(
    body: ProcessRequest,
    conn: sqlite3.Connection = Depends(get_conn),
) -> dict:
    """Processa a variante escolhida (D-03 passo 3): valida→limpa→viabilidade→persiste atômico.

    O serviço adquire a trava AQUI e devolve um relatório "busy" (has_fatal) se ocupado — o
    router só repassa o relatório como JSON, sem decidir nada.
    """
    # Confina ambos os paths do corpo sob a raiz de dados ANTES de qualquer read — sem isso,
    # main_table="/etc/passwd" vira leitura arbitrária de arquivo via pandas (CR-01). A raiz vem
    # de service.DATA_ROOT em tempo de chamada (monkeypatchável no teste), não de um literal.
    confined_raw = _confine(Path(body.raw_dir), service.DATA_ROOT)
    confined_main = _confine(Path(body.main_table), service.DATA_ROOT)
    report = service.ingest(conn, confined_raw, body.turma_name, confined_main)
    return {
        "has_fatal": report.has_fatal,
        "items": [
            {"check": i.check, "severity": i.severity, "message": i.message}
            for i in report.items
        ],
        "dataset_summary": report.dataset_summary,
        "per_assignment": [
            {"assignment_id": s.assignment_id, "trainable": s.trainable}
            for s in report.per_assignment
        ],
    }
