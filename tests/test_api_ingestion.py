"""Testes HTTP do router de ingestão (D-12) — primeiros testes da camada FastAPI.

Cobrem o marshalling HTTP↔service: POST /ingest extrai o zip e devolve variantes SEM tocar a
trava (Lock Timing), POST /ingest/process persiste atômico e devolve o relatório, e o teto de
upload rejeita com 413. Herméticos via api_client (tmp app.db + DATA_ROOT em tmp_path); NUNCA o
CSEDM real. As asserções pinam invariantes (variantes achadas / holder NULL / status do gate),
nunca AUC.
"""

from __future__ import annotations

import io
import zipfile

from edmkt_app.api import ingestion

_MAIN_TABLE = (
    "SubjectID,AssignmentID,ProblemID,CodeStateID,EventType,Score,ServerTimestamp\n"
    "S1,439,1,c1,Run.Program,0.0,2019-03-01T08:00:00Z\n"
    "S1,439,2,c2,Run.Program,1.0,2019-03-01T08:01:00Z\n"
    "S2,439,1,c3,Run.Program,1.0,2019-03-01T08:02:00Z\n"
    "S2,439,2,c4,Run.Program,0.5,2019-03-01T08:03:00Z\n"
)
_CODE_STATES = (
    "CodeStateID,Code\n"
    'c1,"public int f(){return 0;}"\n'
    'c2,"public int g(){return 1;}"\n'
    'c3,"public int h(){return 1;}"\n'
    'c4,"public int k(){return 2;}"\n'
)


def _zip_bytes(main_table: str = _MAIN_TABLE) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("MainTable.csv", main_table)
        zf.writestr("CodeStates/CodeStates.csv", _CODE_STATES)
    return buf.getvalue()


def _holder_pid(conn):
    return conn.execute("SELECT holder_pid FROM pipeline_lock WHERE id=1;").fetchone()[
        "holder_pid"
    ]


def test_upload_detects_variants_without_lock(api_client):
    client, conn = api_client
    resp = client.post(
        "/ingest",
        data={"turma": "Turma X"},
        files={"file": ("upload.zip", _zip_bytes(), "application/zip")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["turma_slug"] == "turma-x"
    assert body["main_tables"]  # achou ao menos uma MainTable
    assert body["code_states"] is not None
    # Detecção é read-only do estado compartilhado: NÃO setou holder_pid (Lock Timing).
    assert _holder_pid(conn) is None


def test_process_persists_and_reports_trainable(api_client):
    client, conn = api_client
    detect = client.post(
        "/ingest",
        data={"turma": "Turma X"},
        files={"file": ("upload.zip", _zip_bytes(), "application/zip")},
    ).json()
    main_table = detect["main_tables"][0]

    resp = client.post(
        "/ingest/process",
        json={"turma_name": "Turma X", "raw_dir": detect["raw_dir"], "main_table": main_table},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["has_fatal"] is False
    # Ambas as classes presentes ⇒ assignment trainable (gate D-09).
    assert body["per_assignment"][0]["trainable"] is True
    # Persistiu pelas portas da Fase 2: 1 turma, 1 assignment.
    n_turmas = conn.execute("SELECT COUNT(*) AS n FROM turma;").fetchone()["n"]
    assert n_turmas == 1
    status = conn.execute("SELECT status FROM assignment;").fetchone()["status"]
    assert status == "trainable"
    # `with lock` liberou a trava ao terminar (SC3).
    assert _holder_pid(conn) is None


def test_process_rejects_path_outside_data_root(api_client, monkeypatch):
    client, _ = api_client
    # Stub de service.ingest que registra chamadas: a asserção forte é que a rejeição acontece
    # ANTES de qualquer read (CR-01) — service.ingest NÃO pode ser chamado para path fora da raiz.
    calls = []
    monkeypatch.setattr(ingestion.service, "ingest", lambda *a, **k: calls.append(a))

    # main_table apontando para /etc/passwd: primitiva de leitura arbitrária se não confinada.
    resp = client.post(
        "/ingest/process",
        json={"turma_name": "X", "raw_dir": str(ingestion.service.DATA_ROOT / "raw"),
              "main_table": "/etc/passwd"},
    )
    assert resp.status_code == 400
    assert calls == []  # rejeição pré-read: o serviço nunca foi invocado

    # raw_dir fora da raiz (ex.: /etc) também é rejeitado sem chamar o serviço.
    resp = client.post(
        "/ingest/process",
        json={"turma_name": "X", "raw_dir": "/etc",
              "main_table": str(ingestion.service.DATA_ROOT / "raw" / "MainTable.csv")},
    )
    assert resp.status_code == 400
    assert calls == []

    # `..` que normaliza para fora da raiz: a guarda resolve ANTES de conferir (não confia na string crua).
    escaping = str(ingestion.service.DATA_ROOT / "raw" / ".." / ".." / "etc" / "passwd")
    resp = client.post(
        "/ingest/process",
        json={"turma_name": "X", "raw_dir": str(ingestion.service.DATA_ROOT / "raw"),
              "main_table": escaping},
    )
    assert resp.status_code == 400
    assert calls == []


def test_upload_over_size_limit_rejected_413(api_client, monkeypatch):
    client, _ = api_client
    # Aperta o teto para um valor minúsculo em vez de subir 512 MiB — exercita o guarda de
    # streaming (T-04-UPLOAD) sem gastar memória/disco.
    monkeypatch.setattr(ingestion, "_MAX_UPLOAD_BYTES", 16)
    resp = client.post(
        "/ingest",
        data={"turma": "Turma X"},
        files={"file": ("upload.zip", _zip_bytes(), "application/zip")},
    )
    assert resp.status_code == 413
