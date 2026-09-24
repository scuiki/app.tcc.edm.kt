"""Os estágios do KCGen-KT: amostra → gera → clusteriza/rotula → Q-matrix → persiste."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from ml.kc_generation.candidate_generation import generate_candidate_kcs
from ml.kc_generation.group_naming import name_kc_group
from ml.kc_generation.kc_grouping import CANDIDATE_GROUP_COUNTS, choose_kc_group_count
from ml.kc_generation.qmatrix_builder import build_qmatrix
from ml.kc_generation.solution_sampling import select_sample_solutions
from edmkt_app import data_layout
from edmkt_app.kc_pipeline.qmatrix_validation import _validate_qmatrix
from edmkt_app.kc_pipeline.transport import _CachedLLM
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.db import transaction
from edmkt_app.values import ProgSnapAssignmentId, TurmaSlug
from edmkt_app.clock import utc_now_iso



def _kc_body(conn, assignment_id: int, job_id: int) -> dict:
    job_repo = repos.KCJobRepository(conn)
    asg_repo = repos.AssignmentRepository(conn)

    asg = asg_repo.get(assignment_id)
    if asg is None:
        raise ValueError(f"assignment {assignment_id} inexistente")
    turma = repos.TurmaRepository(conn).get(asg.turma_id)
    turma_slug = TurmaSlug.from_name(turma.name)
    progsnap_aid = ProgSnapAssignmentId(asg.progsnap_assignment_id)

    job_repo.mark_running(job_id, started_at=utc_now_iso())

    pq = data_layout.cleaned_submissions_path(turma_slug, progsnap_aid)
    df = pd.read_parquet(pq, engine="pyarrow")

    # Pitfall 4: KC-gen vê só código CORRETO (a 1ª submissão correta por aluno×problema sai do
    # select_sample_solutions). Filtrar aqui evita mostrar código errado ao LLM.
    correct_df = df[df["is_correct"] == 1]
    problem_ids = sorted(str(p) for p in correct_df["problem_id"].dropna().unique())

    cache_dir = data_layout.llm_cache_dir(turma_slug, progsnap_aid)
    gen_llm = _CachedLLM(cache_dir, stage="generate")

    # Etapa 2 (por problema): amostra por diversidade → gera KCs pela porta LLM. NoCandidateKCsError de
    # um problema (0 KCs) sobe como falha-dura (D-04, capturada em _run_kc_pipeline).
    job_repo.update_stage(job_id, stage="generate", updated_at=utc_now_iso())
    kc_raw: dict = {}
    for pid in problem_ids:
        pdf = correct_df[correct_df["problem_id"].astype(str) == pid]
        samples = select_sample_solutions(pdf, n=5)
        code_samples = [s["code"] for s in samples]
        kc_raw[pid] = generate_candidate_kcs(int(pid), code_samples, gen_llm)

    # Etapa 3-4: nomes únicos de KC → clusters. Com menos nomes únicos que o MENOR candidato
    # {10,12,15} o silhouette/HAC não se aplica (CR-01, Pitfall 5 estendido): cada nome único
    # vira seu próprio cluster, sem SBERT nem chamada de labeling — caminho real p/ turmas pequenas.
    # Este guard é o DONO da fronteira; choose_kc_group_count só roda quando há candidato viável.
    unique_names: list[str] = []
    for pid in problem_ids:
        for kc in kc_raw[pid]["kcs"]:
            if kc["name"] not in unique_names:
                unique_names.append(kc["name"])

    job_repo.update_stage(job_id, stage="cluster", updated_at=utc_now_iso())
    if len(unique_names) < min(CANDIDATE_GROUP_COUNTS):
        kc_to_cluster = {name: i for i, name in enumerate(unique_names)}
        cluster_names = {i: name for i, name in enumerate(unique_names)}
        n_clusters = len(unique_names)
    else:
        n_clusters, kc_to_cluster, cluster_names = _cluster_and_label(
            unique_names, cache_dir
        )

    kc_clusters = {"n_clusters_selected": n_clusters, "kc_to_cluster": kc_to_cluster}

    # Etapa 5: Q-matrix binária problemas × clusters.
    job_repo.update_stage(job_id, stage="qmatrix", updated_at=utc_now_iso())
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
        asg_repo.set_status(assignment_id, "kc_draft")
        # WR-01: mark_done DENTRO da txn — o flip de status e a conclusão do job são atômicos.
        # Fora dela, uma falha de mark_done deixaria assignment 'kc_draft' + job 'failed'.
        job_repo.mark_done(job_id, updated_at=utc_now_iso())

    return {"n_clusters": n_clusters, "n_problems": len(problem_ids)}


def _cluster_and_label(unique_names: list[str], cache_dir: Path) -> tuple[int, dict, dict]:
    """SBERT-encode → silhouette/HAC → rotula cada cluster pela porta LLM (Etapas 3-4).

    SBERT é importado preguiçosamente (não está em todo ambiente de teste): só é tocado quando
    há nomes suficientes para clusterizar. Devolve (n_clusters, kc_to_cluster, cluster_names)."""
    from sentence_transformers import SentenceTransformer

    embeddings = SentenceTransformer("all-MiniLM-L6-v2").encode(unique_names)
    n_clusters, _scores = choose_kc_group_count(embeddings)

    from ml.kc_generation.kc_grouping import group_similar_kcs

    labels = group_similar_kcs(embeddings, n_clusters)
    members: dict[int, list[str]] = {}
    for name, cid in zip(unique_names, labels):
        members.setdefault(int(cid), []).append(name)

    label_llm = _CachedLLM(cache_dir, stage="label")
    kc_to_cluster: dict[str, int] = {}
    cluster_names: dict[int, str] = {}
    for cid in sorted(members):
        labelled = name_kc_group(members[cid], label_llm, cid)
        cluster_names[cid] = labelled["name"]
        for name in members[cid]:
            kc_to_cluster[name] = cid
    return n_clusters, kc_to_cluster, cluster_names
