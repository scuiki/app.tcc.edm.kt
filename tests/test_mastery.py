"""Testes RED de mastery (DASH-01/02/03) — invariantes, não números mágicos.

Pinam o contrato do módulo puro `edmkt_core.mastery` ANTES de existir (Nyquist: a
implementação dos planos 02-06 nasce GREEN contra estes testes). Filosofia herdada de
test_artifacts.py: asseritar invariantes (ordenação, faixas nos limites, média problem→KC,
regra de risco) em vez de valores específicos de um modelo treinado. Todos FALHAM agora com
ImportError em `edmkt_core.mastery` — é o estado Wave 0 esperado.

A matriz aluno×KC é construída tomando a ÚLTIMA correct_predictions por (user_id, ProblemID)
e fazendo a MÉDIA sobre os problemas que cada KC marca (via Q-matrix) — NUNCA indexando a
saída do modelo por kc_id (Pitfall 2: a cabeça do Code-DKT é por ProblemID, não por KC).
"""

from __future__ import annotations

import pandas as pd
import pytest


def test_bands_classify_at_boundaries():
    # DASH-01: faixas fixas low <0.40 / medium 0.40–0.70 / high >0.70 (prototype, REQUIREMENTS:85).
    # Os limites são o que importa: 0.40 é o piso de medium, 0.70 o teto de medium.
    from edmkt_core.mastery import classify_band

    assert classify_band(0.0) == "low"
    assert classify_band(0.399) == "low"
    assert classify_band(0.40) == "medium"  # limite inferior pertence a medium
    assert classify_band(0.55) == "medium"
    assert classify_band(0.70) == "medium"  # 0.70 ainda é medium; só >0.70 vira high
    assert classify_band(0.7001) == "high"
    assert classify_band(1.0) == "high"


def test_matrix_aggregates_problem_to_kc_by_mean():
    # DASH-01 + Pitfall 2: a mastery de um KC é a MÉDIA das masteries dos problemas que o KC
    # marca. Q-matrix: KC1 → {prob 1, prob 3}; KC2 → {prob 2, prob 3}.
    # Para um aluno com problem-mastery {1: 0.2, 2: 0.8, 3: 0.6}:
    #   KC1 = mean(0.2, 0.6) = 0.4 ; KC2 = mean(0.8, 0.6) = 0.7.
    from edmkt_core.mastery import build_mastery_matrix

    # pred_df no shape de predict_code_dkt: a ÚLTIMA linha por (user_id, ProblemID) é a mastery
    # final daquele problema; uma 1ª tentativa anterior NÃO deve sobrescrever a última.
    pred_df = pd.DataFrame(
        [
            {"user_id": "S1", "skill_name": "1", "correct": 0, "is_first_attempt": True,  "correct_predictions": 0.9},
            {"user_id": "S1", "skill_name": "1", "correct": 0, "is_first_attempt": False, "correct_predictions": 0.2},  # última p/ prob 1
            {"user_id": "S1", "skill_name": "2", "correct": 1, "is_first_attempt": True,  "correct_predictions": 0.8},
            {"user_id": "S1", "skill_name": "3", "correct": 1, "is_first_attempt": True,  "correct_predictions": 0.6},
        ]
    )
    qmatrix = {1: [10], 2: [20], 3: [10, 20]}  # problem_id -> [kc_id...]; KC1=10, KC2=20

    matrix = build_mastery_matrix(pred_df, qmatrix)

    # matrix indexável por (subject_id, kc_id) -> mastery float em [0,1].
    assert matrix[("S1", 10)] == pytest.approx(0.4)  # mean(0.2 [última do prob1], 0.6)
    assert matrix[("S1", 20)] == pytest.approx(0.7)  # mean(0.8, 0.6)


def test_critical_kcs_ascending_by_mean_class_mastery(trained_artifact):
    # DASH-02: KCs críticos = ordenados por mastery MÉDIA da turma, ASCENDENTE (o mais fraco
    # primeiro). Duas turmas sintéticas: KC 'A' média 0.2, KC 'B' média 0.8 → A vem antes de B.
    from edmkt_core.mastery import critical_kcs

    matrix = {
        ("S1", 1): 0.1, ("S2", 1): 0.3,  # KC 1 média 0.2
        ("S1", 2): 0.7, ("S2", 2): 0.9,  # KC 2 média 0.8
    }
    ranked = critical_kcs(matrix)

    kc_order = [kc_id for kc_id, _mean in ranked]
    assert kc_order == [1, 2]  # ascendente: o KC de menor mastery média primeiro
    assert ranked[0][1] == pytest.approx(0.2)
    assert ranked[1][1] == pytest.approx(0.8)


def test_at_risk_students_below_low_band(trained_artifact):
    # DASH-03: aluno em atenção = tem >= N KCs abaixo da faixa low (<0.40). N=3 travado pelo
    # prototype (A4). S_risk tem 3 KCs <0.40 (entra); S_ok tem só 2 (não entra).
    from edmkt_core.mastery import at_risk_students

    matrix = {
        ("S_risk", 1): 0.1, ("S_risk", 2): 0.2, ("S_risk", 3): 0.3, ("S_risk", 4): 0.9,
        ("S_ok",   1): 0.1, ("S_ok",   2): 0.2, ("S_ok",   3): 0.8, ("S_ok",   4): 0.9,
    }
    at_risk = at_risk_students(matrix, threshold_n=3)

    assert "S_risk" in at_risk
    assert "S_ok" not in at_risk


# --- service-level: load → infer → aggregate → persist (plan 06-05, DASH-01/02/03, D-04) ---
# A camada impura (mastery_service) orquestra ArtifactStore.load_version → predict_code_dkt →
# Q-matrix aprovada → o SEAM puro edmkt_core.mastery → persiste em mastery_prediction. Os testes
# abaixo pinam a DELEGAÇÃO (o serviço devolve EXATAMENTE o build_mastery_matrix puro sobre o
# pred_df que ele mesmo inferiu) e o COMPUTE-ONCE (a 2ª chamada não recomputa nem duplica linhas).


def _seed_clean_parquet(ns, data_root, with_compile_errors: bool = False):
    # Monta o Parquet canônico da Fase 3 no caminho que o serviço deriva (_slug(turma)/clean/
    # assignment_<progsnap_aid>.parquet). turma="Turma 6" → "turma-6"; assignment="A439" → 439.
    # Problemas 1/2/3 batem com a Q-matrix do fixture (problema 3 liga ambos os KCs).
    from edmkt_app.ingestion.clean import CANONICAL_COLUMNS

    base = pd.Timestamp("2019-03-01T08:00:00Z")
    java_a = "public int f(int x) { return x + 1; }"
    java_b = "public int g(int a, int b) { int s = a + b; return s; }"
    java_c = "public boolean h(int n) { if (n > 0) { return true; } return false; }"

    def _row(subject, problem, step, score, code, csid):
        return {
            "SubjectID": subject,
            "AssignmentID": 439,
            "ProblemID": problem,
            "CodeStateID": csid,
            "Code": code,
            "Score": score,
            "ServerTimestamp": base + pd.Timedelta(minutes=step),
            "EventType": "Run.Program",
            "correct": int(score == 1.0),
        }

    rows = []
    for si, subj in enumerate(("Sa", "Sb", "Sc")):
        plan = [(1, 0.0, java_a, "x1"), (2, 1.0, java_b, "x2"),
                (1, 1.0, java_a, "x3"), (3, 0.0, java_c, "x4")]
        for step, (pid, score, code, csid) in enumerate(plan):
            rows.append(_row(subj, pid, si * 10 + step, score, code, f"c{si}_{step}"))
        if with_compile_errors:
            # Como o canônico da Fase 3 grava de fato (ALLOWED_EVENTS, D-10): Compile.Error com
            # Java quebrado convive com os Run.Program no MESMO Parquet.
            broken = _row(subj, 1, si * 10 + 5, 0.0, "public int oops( { return ;;; }", "")
            broken["CodeStateID"] = f"e{si}"
            broken["EventType"] = "Compile.Error"
            broken["correct"] = 0
            rows.append(broken)
    df = pd.DataFrame(rows)
    df["ServerTimestamp"] = pd.to_datetime(df["ServerTimestamp"], utc=True)
    df["AssignmentID"] = df["AssignmentID"].astype("Int64")
    df["ProblemID"] = df["ProblemID"].astype("Int64")

    clean_dir = data_root / "turma-6" / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)
    df[CANONICAL_COLUMNS].to_parquet(
        clean_dir / "assignment_439.parquet", engine="pyarrow", index=False
    )


def test_service_matrix_equals_pure_seam(trained_artifact, tmp_path, monkeypatch):
    # DELEGAÇÃO (D-04): a matriz que o serviço persiste é IDÊNTICA a chamar o seam puro
    # build_mastery_matrix sobre o pred_df que o próprio serviço inferiu + a Q-matrix aprovada —
    # o serviço orquestra, não re-implementa a agregação.
    from edmkt_app import mastery_service
    from edmkt_app.mastery_service import inference
    from edmkt_app import settings
    from edmkt_core.mastery import build_mastery_matrix

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    _seed_clean_parquet(trained_artifact, tmp_path)
    conn = trained_artifact.conn

    matrix = mastery_service.compute_mastery(conn, trained_artifact.assignment_id)

    # Oráculo puro: o serviço expõe o pred_df que inferiu; o seam puro sobre ele + a Q-matrix
    # (problem_id → [kc_id...]) deve reproduzir a mesma matriz, célula a célula.
    pred_df = mastery_service.infer_predictions(conn, trained_artifact.assignment_id)
    qdict = {}
    for binding in trained_artifact.qmatrix:
        qdict.setdefault(binding.problem_id, []).append(binding.kc_id)
    expected = build_mastery_matrix(pred_df, qdict)

    assert matrix == pytest.approx(expected)
    assert matrix  # não-vazio: a inferência produziu masteries para ao menos um (aluno, KC)
    for (subject_id, kc_id), value in matrix.items():
        assert isinstance(subject_id, str)
        assert isinstance(kc_id, int)
        assert 0.0 <= value <= 1.0


def test_service_persists_compute_once(trained_artifact, tmp_path, monkeypatch):
    # COMPUTE-ONCE (T-06-11 DoS + correção): a 1ª chamada persiste uma linha por (subject, kc)
    # na mastery_prediction keyed ao artifact; a 2ª chamada NÃO recomputa nem duplica.
    from edmkt_app import mastery_service
    from edmkt_app.mastery_service import inference
    from edmkt_app import settings

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    _seed_clean_parquet(trained_artifact, tmp_path)
    conn = trained_artifact.conn
    artifact_id = trained_artifact.artifact_id

    matrix = mastery_service.compute_mastery(conn, trained_artifact.assignment_id)

    def _row_count():
        return conn.execute(
            "SELECT COUNT(*) AS n FROM mastery_prediction WHERE model_artifact_id = ?;",
            (artifact_id,),
        ).fetchone()["n"]

    after_first = _row_count()
    assert after_first == len(matrix)  # uma linha por (subject, kc) da matriz

    again = mastery_service.compute_mastery(conn, trained_artifact.assignment_id)
    assert _row_count() == after_first  # 2ª chamada não duplica
    assert again == pytest.approx(matrix)  # serve o mesmo resultado


def test_persist_failure_leaves_no_partial_cache(trained_artifact, tmp_path, monkeypatch):
    # CR-01: a conn está em autocommit (db.py:21). Sem uma transação explícita, cada INSERT do
    # loop commitaria sozinho e uma falha no meio deixaria um cache PARCIAL que o guard
    # compute-once (count_by_artifact > 0) serviria para sempre como se fosse a matriz completa.
    # Falhamos o insert DEPOIS da 1ª linha: com a transação, o ROLLBACK desfaz tudo (0 linhas);
    # sem ela, a 1ª linha já commitou e fica órfã (>=1 linha) — este teste RED pega exatamente isso.
    from edmkt_app import mastery_service
    from edmkt_app.mastery_service import inference
    from edmkt_app import settings
    from edmkt_app.persistence import repositories as repos

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    _seed_clean_parquet(trained_artifact, tmp_path)
    conn = trained_artifact.conn
    artifact_id = trained_artifact.artifact_id

    real_insert = repos.MasteryPredictionRepository.insert
    state = {"n": 0}

    def _fail_after_first(self, pred):
        state["n"] += 1
        if state["n"] > 1:
            raise RuntimeError("disk full no insert da mastery (simulado)")
        return real_insert(self, pred)

    monkeypatch.setattr(repos.MasteryPredictionRepository, "insert", _fail_after_first)

    with pytest.raises(RuntimeError):
        mastery_service.compute_mastery(conn, trained_artifact.assignment_id)

    n = conn.execute(
        "SELECT COUNT(*) AS n FROM mastery_prediction WHERE model_artifact_id = ?;",
        (artifact_id,),
    ).fetchone()["n"]
    assert n == 0  # atômico: o write parcial foi revertido, sem cache truncado

    # E o guard compute-once NÃO foi envenenado: uma chamada limpa (sem falha) recomputa
    # a matriz inteira em vez de servir o cache parcial.
    monkeypatch.setattr(repos.MasteryPredictionRepository, "insert", real_insert)
    matrix = mastery_service.compute_mastery(conn, trained_artifact.assignment_id)
    assert matrix
    assert (
        conn.execute(
            "SELECT COUNT(*) AS n FROM mastery_prediction WHERE model_artifact_id = ?;",
            (artifact_id,),
        ).fetchone()["n"]
        == len(matrix)
    )


def test_compute_mastery_resolves_artifact_once(trained_artifact, tmp_path, monkeypatch):
    # WR-02: compute_mastery resolve o artefato UMA vez e o thread em infer_predictions, em vez
    # de deixar infer_predictions re-resolver current_version_id. Se um flip_current concorrente
    # trocasse a versão entre as duas leituras (conn em autocommit), as linhas seriam keyed ao
    # artefato A mas o modelo carregado viria de B — um mismatch silencioso. Simulamos isso
    # fazendo _resolve_current_artifact devolver um artefato DIFERENTE na 2ª chamada e exigimos
    # que o modelo carregado (via load_version) seja o MESMO que keya as linhas persistidas.
    from edmkt_app import mastery_service
    from edmkt_app.mastery_service import inference
    from edmkt_app import settings
    from edmkt_app.persistence import models
    from edmkt_app.persistence.artifacts import ArtifactStore

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    _seed_clean_parquet(trained_artifact, tmp_path)
    conn = trained_artifact.conn

    real_resolve = inference._resolve_current_artifact
    asg, artifact_a = real_resolve(conn, trained_artifact.assignment_id)

    # Um 2º artefato "concorrente" com um artifact_dir distinto e inexistente — se alguém
    # re-resolver e carregar ESTE, load_version vai apontar para um dir que não existe.
    artifact_b = models.ModelArtifact(
        id=artifact_a.id + 999,
        assignment_id=artifact_a.assignment_id,
        version_number=artifact_a.version_number + 1,
        content_hash=artifact_a.content_hash,
        artifact_dir=str(tmp_path / "nonexistent_v999"),
        created_at=artifact_a.created_at,
        first_auc=artifact_a.first_auc,
    )

    calls = {"n": 0}

    def _flipping_resolve(c, aid):
        calls["n"] += 1
        if calls["n"] == 1:
            return asg, artifact_a
        return asg, artifact_b  # "flip" concorrente na 2ª resolução

    monkeypatch.setattr(inference, "_resolve_current_artifact", _flipping_resolve)

    loaded_dirs: list[str] = []
    real_load = ArtifactStore.load_version

    def _spy_load(self, vdir):
        loaded_dirs.append(vdir)
        return real_load(self, vdir)

    monkeypatch.setattr(ArtifactStore, "load_version", _spy_load)

    matrix = mastery_service.compute_mastery(conn, trained_artifact.assignment_id)

    # O modelo carregado tem de ser o artefato A (resolvido uma vez e threaded), NÃO o B do
    # "flip" — senão load_version teria recebido o dir inexistente de B.
    assert loaded_dirs == [artifact_a.artifact_dir]
    # E as linhas persistidas são keyed a A — consistente com o modelo de fato carregado.
    n_a = conn.execute(
        "SELECT COUNT(*) AS n FROM mastery_prediction WHERE model_artifact_id = ?;",
        (artifact_a.id,),
    ).fetchone()["n"]
    assert n_a == len(matrix)


def test_infer_predictions_orphan_turma_raises_valueerror(trained_artifact, tmp_path, monkeypatch):
    # WR-01: se a turma do assignment sumiu, infer_predictions chamava turma.name e explodia em
    # AttributeError opaco. A guarda levanta um ValueError claro ("turma N inexistente").
    from edmkt_app import mastery_service
    from edmkt_app.mastery_service import inference
    from edmkt_app import settings

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    _seed_clean_parquet(trained_artifact, tmp_path)
    conn = trained_artifact.conn

    # Remove a turma (FK desligada só p/ o DELETE: o órfão surge de uma conexão sem enforcement).
    conn.execute("PRAGMA foreign_keys=OFF;")
    conn.execute("DELETE FROM turma WHERE id = ?;", (trained_artifact.turma_id,))
    conn.execute("PRAGMA foreign_keys=ON;")

    with pytest.raises(ValueError, match="turma .* inexistente"):
        mastery_service.infer_predictions(conn, trained_artifact.assignment_id)


def test_inference_stream_excludes_compile_errors(trained_artifact, tmp_path, monkeypatch):
    """A inferência lê o MESMO Parquet canônico do treino — e precisa do MESMO filtro.

    Espelha test_train_cli.test_compile_errors_never_reach_the_training_stream do lado da
    leitura: treinar só com Run.Program e depois inferir sobre o stream misto alimentaria o
    modelo com eventos que ele nunca viu no treino, e a matriz aluno×KC do dashboard sairia
    de uma distribuição diferente da que produziu o AUC exibido na moldura de incerteza.
    """
    from edmkt_app import mastery_service
    from edmkt_app.mastery_service import inference
    from edmkt_app import settings

    monkeypatch.setattr(settings, "DATA_ROOT", tmp_path)
    _seed_clean_parquet(trained_artifact, tmp_path, with_compile_errors=True)

    seen = {}
    real_build_sequences = inference.build_sequences

    def _spy(df, progsnap_aid, *args, **kwargs):
        seen["event_types"] = set(df["EventType"].unique())
        return real_build_sequences(df, progsnap_aid, *args, **kwargs)

    monkeypatch.setattr(inference, "build_sequences", _spy)
    mastery_service.infer_predictions(trained_artifact.conn, trained_artifact.assignment_id)

    assert seen["event_types"] == {"Run.Program"}
