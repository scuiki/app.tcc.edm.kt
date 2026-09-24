# Versões de modelo em disco, write-once, versão monótona, hash estável e leitura confinada.

from __future__ import annotations

import json
import pickle
import sqlite3
from pathlib import Path

import pandas as pd
import pytest
import torch

from api.assignments.domain.value_objects.classroom_slug import ClassroomSlug
from api.assignments.domain.value_objects.progsnap_assignment_id import ProgSnapAssignmentId
from api.model_training.domain.value_objects.training_outcome import TrainingOutcome
from api.model_training.domain.value_objects.training_dataset import TrainingDataset
from api.model_training.infrastructure.repositories.sqlite_trained_model_repository import (
    SqliteTrainedModelRepository,
)
from api.model_training.infrastructure.implementations.trained_model_file_store import (
    ModelVersionFiles,
    TrainedModelFileStore,
)


def _save(conn, classroom_id: int, assignment_id: int, model, vocab, config) -> dict:
    # Grava pela TrainedModelFileStore real e devolve {version_number, artifact_id, dir}.
    model_id = TrainedModelFileStore(conn).save(
        TrainingDataset(
            events=pd.DataFrame(),
            classroom_slug=ClassroomSlug("turma-a"),
            progsnap_assignment_id=ProgSnapAssignmentId(1),
            classroom_id=classroom_id,
        ),
        assignment_id,
        TrainingOutcome(
            model=model, vocab=vocab, hyperparameters=config, first_attempt_auc=None,
            java_parse_rate=1.0,
        ),
    )
    saved = SqliteTrainedModelRepository(sqlite3_connection(conn)).get(model_id)
    return {"version_number": saved.version_number, "artifact_id": model_id, "dir": saved.model_dir}


def sqlite3_connection(conn):
    return getattr(conn, "_real", conn)


def _seed_turma_assignment(conn) -> tuple[int, int]:
    # classroom + assignment em SQL puro; devolve (classroom_id, assignment_id).
    classroom_id = conn.execute(
        "INSERT INTO classroom (name, created_at) VALUES ('Turma A', 't0');"
    ).lastrowid
    return classroom_id, _add_assignment(conn, classroom_id, "A1")


def _add_assignment(conn, classroom_id: int, name: str) -> int:
    return conn.execute(
        "INSERT INTO assignment (classroom_id, name, created_at) VALUES (?, ?, 't0');",
        (classroom_id, name),
    ).lastrowid


def test_save_writes_blob_and_sidecars(tmp_path, tiny_model, tiny_vocab, tiny_config):
    # save grava os 3 arquivos e o meta com input/output_dim; tiny_model é stand-in, não o real.
    import pathlib

    store = ModelVersionFiles(tmp_path / "data")
    result = store.write(
        assignment_id=1,
        version_number=1,
        model=tiny_model,
        vocab=tiny_vocab,
        config=tiny_config,
    )

    vdir = pathlib.Path(result["dir"])
    assert (vdir / "model.pt").exists()
    assert (vdir / "vocab.pkl").exists()
    assert (vdir / "config.json").exists()

    reloaded_vocab = pickle.loads((vdir / "vocab.pkl").read_bytes())
    meta = json.loads((vdir / "config.json").read_text())
    assert reloaded_vocab == tiny_vocab
    for key in tiny_config:
        assert meta[key] == tiny_config[key]
    assert meta["node_count"] == tiny_vocab["node_count"]
    assert meta["path_count"] == tiny_vocab["path_count"]
    # input_dim/output_dim derivados do objeto vivo, no CodeDKTModel real input_dim != output_dim.
    assert meta["input_dim"] == tiny_model.input_dim
    assert meta["output_dim"] == tiny_model.fc.out_features == meta["n_problems"]

    # state_dict relido bate com o gravado (só os pesos foram salvos, não o nn.Module).
    saved_sd = torch.load(vdir / "model.pt", map_location="cpu")
    for name, tensor in tiny_model.state_dict().items():
        assert torch.equal(saved_sd[name], tensor)


def test_version_monotonic_per_scope(tmp_db, data_root, tiny_model, tiny_vocab, tiny_config):
    # 3 versões do mesmo assignment geram v1,v2,v3; outro assignment recomeça em v1 (escopo turma).
    conn = tmp_db
    classroom_id, assignment_a = _seed_turma_assignment(conn)
    assignment_b = _add_assignment(conn, classroom_id, "A2")

    versions_a = [
        _save(conn, classroom_id, assignment_a, tiny_model, tiny_vocab, tiny_config)
        for _ in range(3)
    ]
    assert [v["version_number"] for v in versions_a] == [1, 2, 3]

    # segundo assignment recomeça em v1, escopo por (turma, assignment).
    version_b = _save(conn, classroom_id, assignment_b, tiny_model, tiny_vocab, tiny_config)
    assert version_b["version_number"] == 1

    # as linhas estão de fato persistidas e ordenáveis pelo version_number.
    rows = conn.execute(
        "SELECT version_number FROM model_artifact WHERE assignment_id=? ORDER BY version_number;",
        (assignment_a,),
    ).fetchall()
    assert [r["version_number"] for r in rows] == [1, 2, 3]


def test_write_once_refuses_overwrite(tmp_path, tiny_model, tiny_vocab, tiny_config):
    # Re-gravar uma versão existente falha (mkdir sem exist_ok); nenhum byte do v<N> é alterado.
    store = ModelVersionFiles(tmp_path / "data")
    first = store.write(
        assignment_id=1, version_number=1,
        model=tiny_model, vocab=tiny_vocab, config=tiny_config,
    )
    weights_before = (__import__("pathlib").Path(first["dir"]) / "model.pt").read_bytes()

    with pytest.raises(FileExistsError):
        store.write(
            assignment_id=1, version_number=1,
            model=tiny_model, vocab=tiny_vocab, config=tiny_config,
        )

    # write-once, o blob anterior segue intacto após a tentativa recusada.
    weights_after = (__import__("pathlib").Path(first["dir"]) / "model.pt").read_bytes()
    assert weights_after == weights_before


def test_content_hash_stable_and_dedup(tmp_path, tiny_model, tiny_vocab, tiny_config):
    # Dois saves iguais produzem o mesmo content_hash; a duplicata não bloqueia a nova versão.
    store = ModelVersionFiles(tmp_path / "data")
    h1 = store.write(
        assignment_id=1, version_number=1,
        model=tiny_model, vocab=tiny_vocab, config=tiny_config,
    )["content_hash"]
    h2 = store.write(
        assignment_id=1, version_number=2,
        model=tiny_model, vocab=tiny_vocab, config=tiny_config,
    )["content_hash"]

    # mesmos bytes -> mesmo hash, mas v2 foi criada do mesmo jeito (dedup avisa, não bloqueia).
    assert h1 == h2
    assert len(h1) == 64  # sha256 hexdigest


def test_reload_contract_no_size_mismatch(tmp_path):
    # Reconstrói um CodeDKTModel real via meta.json e load_state_dict sem RuntimeError de shape.
    from ml.code_dkt.model import CodeDKTModel

    # CodeDKTModel real, input_dim=2M e output_dim=M, distintos.
    M = 2  # n_problems = M; input_dim = 2M
    model = CodeDKTModel(
        input_dim=2 * M,
        hidden_dim=8,
        output_dim=M,
        node_count=4,
        path_count=3,
        dropout=0.1,
        R=4,
        node_embed_dim=6,
        path_embed_dim=6,
    )
    vocab = {"token_to_idx": {}, "path_to_idx": {}, "node_count": 4, "path_count": 3}
    config = {"hidden_dim": 8, "dropout": 0.1, "R": 4, "node_embed_dim": 6, "path_embed_dim": 6}

    store = ModelVersionFiles(tmp_path / "data")
    result = store.write(
        assignment_id=1, version_number=1,
        model=model, vocab=vocab, config=config,
    )
    # não deve levantar RuntimeError de shape mismatch ao reconstruir + load_state_dict.
    loaded, _, meta = store.read(result["dir"])
    assert meta["n_problems"] == M
    assert meta["input_dim"] == 2 * M
    assert isinstance(loaded, CodeDKTModel)
    # o state_dict reconstruído bate com o original (contrato de reload completo, sem mismatch).
    for name, tensor in model.state_dict().items():
        assert torch.equal(loaded.state_dict()[name], tensor)


def test_persist_failure_does_not_block_next_version(
    tmp_db, data_root, tiny_model, tiny_vocab, tiny_config
):
    # Se o INSERT falha após o blob escrito, o v<N> não pode ficar órfão (senão o save falha depois)
    import pathlib

    conn = tmp_db
    classroom_id, assignment_id = _seed_turma_assignment(conn)

    # Connection.execute é read-only (objeto C); um proxy intercepta só o INSERT do model_artifact.
    class _FailOnceInsertProxy:
        def __init__(self, real):
            self._real = real
            self._armed = True

        def execute(self, sql, *args, **kwargs):
            if self._armed and sql.lstrip().upper().startswith("INSERT INTO MODEL_ARTIFACT"):
                self._armed = False  # só falha uma vez
                raise sqlite3.OperationalError("disk full at INSERT (simulado)")
            return self._real.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self._real, name)

    proxy = _FailOnceInsertProxy(conn)

    # (a) a 1ª persist() propaga a exceção do INSERT.
    with pytest.raises(sqlite3.OperationalError):
        _save(proxy, classroom_id, assignment_id, tiny_model, tiny_vocab, tiny_config)

    # (b) nenhum v1 órfão sobra no FS (rmtree desfez o blob); layout é <base>/<assignment_id>/v<N>.
    v1 = data_root / "turma-a" / "models" / str(assignment_id) / "v1"
    assert not v1.exists()

    # (c) a 2ª persist() sucede e devolve version_number==1, o slot foi liberado, não travado.
    result = _save(conn, classroom_id, assignment_id, tiny_model, tiny_vocab, tiny_config)
    assert result["version_number"] == 1

    # (d) a única linha persistida tem version_number == 1.
    rows = conn.execute(
        "SELECT version_number FROM model_artifact WHERE assignment_id=? ORDER BY version_number;",
        (assignment_id,),
    ).fetchall()
    assert [r["version_number"] for r in rows] == [1]


def test_path_stays_under_base(tmp_path, tiny_model, tiny_vocab, tiny_config):
    # O path resolvido fica sob base (sem traversal). Componentes vêm de IDs inteiros internos.
    store = ModelVersionFiles(tmp_path / "data")
    result = store.write(
        assignment_id=1, version_number=1,
        model=tiny_model, vocab=tiny_vocab, config=tiny_config,
    )
    base = (tmp_path / "data").resolve()
    assert str((base)) in str(__import__("pathlib").Path(result["dir"]).resolve())


def test_load_version_refuses_dir_outside_base(tmp_path):
    # vocab.pkl usa pickle irrestrito; sem a guarda, um artifact_dir adulterado rodaria RCE.
    import pathlib

    base = tmp_path / "data"
    base.mkdir()
    store = ModelVersionFiles(base)

    # Diretório fora de base, com vocab.pkl cujo unpickle grava um sentinela (RCE benigna)
    evil_dir = tmp_path / "evil"
    evil_dir.mkdir()
    sentinel = tmp_path / "PWNED"

    class _Payload:
        def __reduce__(self):
            return (pathlib.Path(str(sentinel)).touch, ())

    (evil_dir / "config.json").write_text("{}")
    with open(evil_dir / "vocab.pkl", "wb") as f:
        pickle.dump(_Payload(), f)

    with pytest.raises(ValueError, match="fora da raiz"):
        store.read(str(evil_dir))

    # O efeito colateral do pickle não ocorreu, a guarda barrou antes de qualquer pickle.load.
    assert not sentinel.exists()


# --- uma raiz só para o store, sem segmento "models" repetido -------------------------


def test_version_dir_has_no_repeated_models_segment(tmp_db, data_root, tiny_model, tiny_vocab, tiny_config):
    # A raiz duplicava "models"; a guarda de traversal acabava valendo também sobre data/<turma>/raw
    classroom_id, assignment_id = _seed_turma_assignment(tmp_db)

    persisted = _save(tmp_db, classroom_id, assignment_id, tiny_model, tiny_vocab, tiny_config)

    vdir = Path(persisted["dir"])
    assert [p for p in vdir.parts if p == "models"] == ["models"]
    assert vdir == (data_root / "turma-a" / "models" / str(assignment_id) / "v1").resolve()


def test_reader_and_writer_agree_on_the_root(tmp_path):
    # Leitor e escritor devem confinar sob a mesma raiz (senão a guarda vale sobre data/ inteiro).
    from ml.code_dkt.model import CodeDKTModel

    M = 2
    model = CodeDKTModel(
        input_dim=2 * M, hidden_dim=8, output_dim=M, node_count=4, path_count=3,
        dropout=0.1, R=4, node_embed_dim=6, path_embed_dim=6,
    )
    vocab = {"token_to_idx": {}, "path_to_idx": {}, "node_count": 4, "path_count": 3}
    config = {"hidden_dim": 8, "dropout": 0.1, "R": 4, "node_embed_dim": 6, "path_embed_dim": 6}

    data_root = tmp_path / "data"
    base = data_root / "turma-x" / "models"
    written = ModelVersionFiles(base).write(
        assignment_id=1, version_number=1, model=model, vocab=vocab, config=config
    )

    # Mesma raiz, aceita.
    _loaded, reloaded_vocab, _meta = ModelVersionFiles(base).read(written["dir"])
    assert reloaded_vocab == vocab

    # Raiz larga (o defeito) deixaria artifact_dir dentro de raw/ passar pela guarda; a certa recusa
    raw_dir = data_root / "turma-x" / "raw" / "forjado"
    raw_dir.mkdir(parents=True)
    with pytest.raises(ValueError, match="fora da raiz"):
        ModelVersionFiles(base).read(str(raw_dir))
