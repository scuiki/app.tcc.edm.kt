"""CLI de KC-gen headless: o corpo do KCGen-KT isolado-por-processo (KC-01/KC-04, D-04/D-05).

`python -m edmkt_app.kc_pipeline --assignment N --job-id J` é o processo OS que o handler
FastAPI (api/kc.py) dispara. Espelha train.py: adquire a `PipelineLock` como PRIMEIRO ato
(D-05) — KC-gen e treino NUNCA correm juntos —, lê o Parquet canônico da Fase 3 por
AssignmentID do ProgSnap2 (Pitfall 3), filtra as amostras primeira-correta (Pitfall 4), roda
o pipeline puro (edmkt_core.kc) pelo transporte `claude` (llm.claude_cli) com o cache de FS
(kc_cache), valida o conteúdo (KC-04) e, no sucesso, persiste kc+qmatrix atomicamente e flipa
`assignment.status` para 'kc_draft' (D-06). Numa falha de conteúdo após N tentativas o job
inteiro marca `failed` e NADA parcial é persistido (D-04).

O subprocess abre a SUA conexão SQLite (`connect`), NUNCA compartilha objeto Python com o web
(Pitfall 2): a coordenação é só pela linha `pipeline_lock` + WAL. `edmkt_core.kc` é só
ORQUESTRADO — o transporte LLM é injetado pela porta (DIP).
"""

from __future__ import annotations

import argparse
import os
import re
import sys
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
from edmkt_app.kc_cache import PROMPT_VERSION, cache_get, cache_put, kc_input_hash
from edmkt_app.llm.claude_cli import ClaudeCLIClient
from edmkt_app.llm.validation import EmptyContentError, call_with_retry, validate_kc_result
from edmkt_app.persistence import connect
from edmkt_app.persistence import models
from edmkt_app.persistence import repositories as repos
from edmkt_app.persistence.db import transaction
from edmkt_app.persistence.lock import PipelineLock

# Raiz do FS de dados; resolvida em path absoluto no main() para não depender do cwd herdado do
# web (Pitfall 2). Override por teste.
DATA_ROOT = Path("data")
DB_PATH = "app.db"

# Modelo congelado do TCC 1 (D-01/A4): id pinado, não o alias `haiku`, para fidelidade científica.
MODEL_ID = "claude-haiku-4-5-20251001"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(name: str) -> str:
    # Mesma forma de service._slug / train._slug: o diretório da turma vem do slug interno,
    # nunca de nome de upload.
    s = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return s or "turma"


def _progsnap_aid(assignment_name: str) -> int:
    # Parquet name = AssignmentID do ProgSnap2 (sufixo de "Assignment <N>"), NÃO assignment.id
    # do banco (Pitfall 3). build_sequences/service._persist_atomic usam o mesmo id.
    m = re.search(r"(\d+)", assignment_name)
    if m is None:
        raise ValueError(f"AssignmentID não derivável do nome: {assignment_name!r}")
    return int(m.group(1))


def _llm_generate(system: str, prompt: str, schema: dict) -> dict:
    """Porta única para o `claude` (D-01): chamada single-shot text→JSON pelo transporte CLI.

    É o seam que a orquestração injeta como LLMClient e que os testes monkeypatcham — nenhum
    teste cruza para o binário real (T-05-01). cwd neutro corta o contexto CLAUDE.md (Pitfall 1)."""
    return ClaudeCLIClient(model=MODEL_ID).generate(system, prompt, schema)


class _CachedLLM:
    """Adapter LLMClient (DIP) com cache fino + retry, por-problema/por-cluster (D-02/D-04).

    Cada `generate` deriva uma chave de hash do (model, prompt_version, payload) e consulta o
    cache de FS antes de chamar; um hit pula a chamada inteiramente. As chamadas ao `claude`
    passam pelo `_llm_generate` resolvido em runtime (`globals()[...]`) para que o monkeypatch
    de teste sobre o módulo tenha efeito. call_with_retry só repete erro transiente (D-04)."""

    def __init__(self, cache_dir: Path, stage: str) -> None:
        self._cache_dir = cache_dir
        self._stage = stage

    def generate(self, system: str, prompt: str, schema: dict) -> dict:
        key = kc_input_hash(MODEL_ID, PROMPT_VERSION, prompt)
        cache_id = f"{self._stage}:{key}"
        cached = cache_get(self._cache_dir, problem_id=cache_id, key=key)
        if cached is not None:
            return cached["parsed"]

        # Resolve _llm_generate no módulo em tempo de chamada — o teste o monkeypatcha (raising
        # False), e um default ligado em def-time ignoraria o patch.
        fn = globals()["_llm_generate"]
        parsed = call_with_retry(lambda: fn(system, prompt, schema))

        cache_put(
            self._cache_dir,
            problem_id=cache_id,
            key=key,
            record={"model_id": MODEL_ID, "prompt_version": PROMPT_VERSION, "parsed": parsed},
        )
        return parsed


def _kc_cache_dir(turma_slug: str, progsnap_aid: int) -> Path:
    # Diretório de cache derivado do slug interno + aid (nunca input de usuário) — sem traversal
    # (KC-04). Espelha data/<slug>/kc/ dos artefatos do TCC.
    return DATA_ROOT / turma_slug / "kc" / f"assignment_{progsnap_aid}"


def _kc_body(conn, assignment_id: int, job_id: int) -> dict:
    job_repo = repos.KCJobRepository(conn)
    asg_repo = repos.AssignmentRepository(conn)

    asg = asg_repo.get(assignment_id)
    if asg is None:
        raise ValueError(f"assignment {assignment_id} inexistente")
    turma = repos.TurmaRepository(conn).get(asg.turma_id)
    turma_slug = _slug(turma.name)
    progsnap_aid = _progsnap_aid(asg.name)

    job_repo.mark_running(job_id, started_at=_now_iso())

    pq = DATA_ROOT / turma_slug / "clean" / f"assignment_{progsnap_aid}.parquet"
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

    job_repo.mark_done(job_id, updated_at=_now_iso())
    return {"n_clusters": n_clusters, "n_problems": len(problem_ids)}


def _cluster_and_label(unique_names: list[str], cache_dir: Path) -> tuple[dict, dict, dict]:
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


def _validate_qmatrix(qmatrix: pd.DataFrame, problem_ids: list[str]) -> None:
    """≥1 KC por problema na Q-matrix completa (KC-04). Falha ⇒ EmptyContentError ⇒ hard-fail.

    É o "validar tudo, depois persistir" promovido a falha-dura de job (D-04): uma linha
    toda-zero (problema sem nenhum KC mapeado) reprova a Q-matrix inteira — nada parcial entra."""
    if not problem_ids or qmatrix.empty:
        raise EmptyContentError("Q-matrix vazia: nenhum problema correto gerou KCs")
    for pid in problem_ids:
        if int(qmatrix.loc[pid].sum()) < 1:
            raise EmptyContentError(f"problema {pid} ficou sem nenhum KC")


def _run_kc_pipeline(conn, assignment_id: int, job_id: int) -> dict | None:
    """Adquire a trava (1º ato, D-05) e roda o KC-gen; em falha marca o job e libera a trava.

    Retorna o dict de resultado no sucesso, ou None quando a trava está ocupada por um dono vivo
    (segundo perdedor marca seu próprio job 'busy') ou o pipeline falhou — o estado de falha vive
    todo no KCJob (D-04), sem Q-matrix parcial."""
    job_repo = repos.KCJobRepository(conn)
    # Lock é o PRIMEIRO ato — KC-gen nunca concorre com training (D-05/MODEL-03).
    lock = PipelineLock(conn).acquire("kc_gen", job_id=job_id)
    if not lock:
        job_repo.mark_failed(job_id, "pipeline busy")
        return None
    with lock:  # release garantido ao sair E sob exceção (SC3)
        try:
            return _kc_body(conn, assignment_id, job_id)
        except Exception as e:
            # Conteúdo-vazio (EmptyContentError/EmptyKCError) ou qualquer exceção: job falha e
            # NADA parcial é persistido (D-04) — a txn de persistência nem chegou a abrir, ou
            # deu ROLLBACK. O assignment segue 'trainable' (nunca foi flipado).
            job_repo.mark_failed(job_id, str(e))
            return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m edmkt_app.kc_pipeline")
    parser.add_argument("--assignment", type=int, required=True, help="assignment.id (SQLite)")
    parser.add_argument("--job-id", type=int, required=True, help="kc_job.id (SQLite)")
    args = parser.parse_args(argv)

    # Paths absolutos do env, não do cwd herdado (Pitfall 2): web e subprocess veem o MESMO
    # app.db e data/.
    global DATA_ROOT, DB_PATH
    DB_PATH = os.environ.get("EDMKT_DB_PATH", str(Path(DB_PATH).resolve()))
    DATA_ROOT = Path(os.environ.get("EDMKT_DATA_ROOT", str(DATA_ROOT.resolve())))

    conn = connect(DB_PATH)  # o subprocess abre a SUA conexão (Pitfall 2)
    result = _run_kc_pipeline(conn, args.assignment, args.job_id)
    return 0 if result is not None else 1


if __name__ == "__main__":
    sys.exit(main())
