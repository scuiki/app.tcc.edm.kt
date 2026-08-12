"""Os estágios do KCGen-KT: amostra → gera → clusteriza/rotula → Q-matrix → persiste."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from edmkt_core.kc import (
    CANDIDATE_N_CLUSTERS,
    build_qmatrix,
    diversity_sample,
    generate_kcs_for_problem,
    label_cluster,
    select_best_n_clusters,
)
from edmkt_app import settings
from edmkt_app.kc_pipeline.qmatrix_validation import _validate_qmatrix
from edmkt_app.kc_pipeline.transport import _CachedLLM, _kc_cache_dir
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.db import transaction
from edmkt_app.values import ProgSnapAssignmentId, TurmaSlug


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kc_body(conn, assignment_id: int, job_id: int) -> dict:
    job_repo = repos.KCJobRepository(conn)
    asg_repo = repos.AssignmentRepository(conn)

    asg = asg_repo.get(assignment_id)
    if asg is None:
        raise ValueError(f"assignment {assignment_id} inexistente")
    turma = repos.TurmaRepository(conn).get(asg.turma_id)
    turma_slug = TurmaSlug.from_name(turma.name)
    progsnap_aid = ProgSnapAssignmentId.from_name(asg.name)

    job_repo.mark_running(job_id, started_at=_now_iso())

    pq = settings.DATA_ROOT / turma_slug / "clean" / f"assignment_{progsnap_aid}.parquet"
    df = pd.read_parquet(pq, engine="pyarrow")

    # Pitfall 4: KC-gen vê só código CORRETO (a 1ª submissão correta por aluno×problema sai do
    # diversity_sample). Filtrar aqui evita mostrar código errado ao LLM.
    correct_df = df[df["correct"] == 1]
    problem_ids = sorted(str(p) for p in correct_df["ProblemID"].dropna().unique())

    cache_dir = _kc_cache_dir(turma_slug, progsnap_aid)
    gen_llm = _CachedLLM(cache_dir, stage="generate")

    # Etapa 2 (por problema): amostra por diversidade → gera KCs pela porta LLM. EmptyKCError de
    # um problema (0 KCs) sobe como falha-dura (D-04, capturada em _run_kc_pipeline).
    job_repo.update_stage(job_id, stage="generate", updated_at=_now_iso())
    kc_raw: dict = {}
    for pid in problem_ids:
        pdf = correct_df[correct_df["ProblemID"].astype(str) == pid]
        samples = diversity_sample(pdf, n=5)
        code_samples = [s["code"] for s in samples]
        kc_raw[pid] = generate_kcs_for_problem(int(pid), code_samples, gen_llm)

    # Etapa 3-4: nomes únicos de KC → clusters. Com menos nomes únicos que o MENOR candidato
    # {10,12,15} o silhouette/HAC não se aplica (CR-01, Pitfall 5 estendido): cada nome único
    # vira seu próprio cluster, sem SBERT nem chamada de labeling — caminho real p/ turmas pequenas.
    # Este guard é o DONO da fronteira; select_best_n_clusters só roda quando há candidato viável.
    unique_names: list[str] = []
    for pid in problem_ids:
        for kc in kc_raw[pid]["kcs"]:
            if kc["name"] not in unique_names:
                unique_names.append(kc["name"])

    job_repo.update_stage(job_id, stage="cluster", updated_at=_now_iso())
    if len(unique_names) < min(CANDIDATE_N_CLUSTERS):
        kc_to_cluster = {name: i for i, name in enumerate(unique_names)}
        cluster_names = {i: name for i, name in enumerate(unique_names)}
        n_clusters = len(unique_names)
    else:
        n_clusters, kc_to_cluster, cluster_names = _cluster_and_label(
            unique_names, cache_dir
        )

    kc_clusters = {"n_clusters_selected": n_clusters, "kc_to_cluster": kc_to_cluster}

    # Etapa 5: Q-matrix binária problemas × clusters.
    job_repo.update_stage(job_id, stage="qmatrix", updated_at=_now_iso())
    qmatrix = build_qmatrix(problem_ids, kc_raw, kc_clusters)

    # Validar-tudo-depois-persistir (D-04): cada problema precisa de ≥1 KC ANTES de abrir a txn.
    # Falha aqui ⇒ EmptyContentError ⇒ job failed, NADA persistido.
    _validate_qmatrix(qmatrix, problem_ids)

    # Persistência atômica (espelha service._persist_atomic): kc rows + qmatrix rows numa txn,
    # depois flipa o status. O dict de retorno some com o subprocess; a linha SQLite é a ponte.
    with transaction(conn):
        kc_id_by_cluster: dict[int, int] = {}
        kc_repo = repos.KCRepository(conn)
        for cid in sorted(cluster_names):
            kc_id_by_cluster[cid] = kc_repo.insert(
                models.KC(
                    id=None,
                    assignment_id=assignment_id,
                    name=cluster_names[cid],
                    kc_index=cid,  # id do cluster 0..N — round-trip fiel c/ artefatos TCC (D-06)
                )
            )
        qm_repo = repos.QMatrixRepository(conn)
        for pid in problem_ids:
            row = qmatrix.loc[pid]
            for cid in range(n_clusters):
                if int(row[f"kc_{cid}"]) == 1:
                    qm_repo.insert(
                        models.QMatrix(
                            id=None,
                            assignment_id=assignment_id,
                            kc_id=kc_id_by_cluster[cid],
                            problem_id=int(pid),
                        )
                    )
        # D-06: o assignment só flipa no fim, dentro da mesma txn da persistência.
        conn.execute(
            "UPDATE assignment SET status='kc_draft' WHERE id=?;", (assignment_id,)
        )
        # WR-01: mark_done DENTRO da txn — o flip de status e a conclusão do job são atômicos.
        # Fora dela, uma falha de mark_done deixaria assignment 'kc_draft' + job 'failed'.
        job_repo.mark_done(job_id, updated_at=_now_iso())

    return {"n_clusters": n_clusters, "n_problems": len(problem_ids)}


def _cluster_and_label(unique_names: list[str], cache_dir: Path) -> tuple[int, dict, dict]:
    """SBERT-encode → silhouette/HAC → rotula cada cluster pela porta LLM (Etapas 3-4).

    SBERT é importado preguiçosamente (não está em todo ambiente de teste): só é tocado quando
    há nomes suficientes para clusterizar. Devolve (n_clusters, kc_to_cluster, cluster_names)."""
    from sentence_transformers import SentenceTransformer

    embeddings = SentenceTransformer("all-MiniLM-L6-v2").encode(unique_names)
    n_clusters, _scores = select_best_n_clusters(embeddings)

    from edmkt_core.kc.clustering import _cluster_with_n

    labels = _cluster_with_n(embeddings, n_clusters)
    members: dict[int, list[str]] = {}
    for name, cid in zip(unique_names, labels):
        members.setdefault(int(cid), []).append(name)

    label_llm = _CachedLLM(cache_dir, stage="label")
    kc_to_cluster: dict[str, int] = {}
    cluster_names: dict[int, str] = {}
    for cid in sorted(members):
        labelled = label_cluster(members[cid], label_llm, cid)
        cluster_names[cid] = labelled["name"]
        for name in members[cid]:
            kc_to_cluster[name] = cid
    return n_clusters, kc_to_cluster, cluster_names
