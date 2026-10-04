# IKnowledgeComponentGenerator sobre o KCGen-KT, amostra, gera, agrupa/nomeia, Q-matrix.
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Callable, Hashable, TypeVar

import numpy as np
import pandas as pd

from api.knowledge_components.domain.interfaces.knowledge_component_generator import (
    GeneratedKnowledgeComponents,
)
from api.knowledge_components.infrastructure.implementations.kc_generation_model import (
    KC_GENERATION_MODEL_ID,
    PROMPT_VERSION,
)
from api.knowledge_components.infrastructure.implementations.llm_response_cache import (
    CachedLLMClient,
)
from api.shared.infrastructure.filesystem import data_layout
from ml.kc_generation.candidate_generation import generate_candidate_kcs
from ml.kc_generation.embedding_models import SBERT_MODEL, SBERT_REVISION, embed_solutions
from ml.kc_generation.group_naming import name_kc_group
from ml.kc_generation.kc_grouping import (
    CANDIDATE_GROUP_COUNTS,
    choose_kc_group_count,
    group_similar_kcs,
)
from ml.kc_generation.llm_client import InvalidLLMResponseError, LLMClient
from ml.kc_generation.qmatrix_builder import build_qmatrix
from ml.kc_generation.solution_sampling import select_sample_solutions

# As chamadas de um estágio são independentes, e mais do que isso esbarra no limite da assinatura
LLM_CONCURRENCY = 4

_Key = TypeVar("_Key", bound=Hashable)
_Result = TypeVar("_Result")


def run_in_parallel(
    tasks: dict[_Key, Callable[[], _Result]],
    on_progress: Callable[[int, int], None],
) -> dict[_Key, _Result]:
    # Os resultados voltam pela chave, então a ordem de chegada nunca muda o que o KCGen-KT vê
    results: dict[_Key, _Result] = {}
    total = len(tasks)
    on_progress(0, total)
    with ThreadPoolExecutor(max_workers=LLM_CONCURRENCY) as pool:
        futures = {pool.submit(task): key for key, task in tasks.items()}
        try:
            # O progresso é gravado aqui, na thread que chamou, nunca em duas threads ao mesmo tempo
            for future in as_completed(futures):
                results[futures[future]] = future.result()
                on_progress(len(results), total)
        except BaseException:
            # Uma falha derruba o job inteiro, então as chamadas que nem começaram não saem
            pool.shutdown(wait=True, cancel_futures=True)
            raise
    return results


def _generate_for_problem(
    problem_id: str, solutions: list[str], statement: str | None, llm: LLMClient
) -> list[dict[str, str]]:
    # A mensagem da resposta inválida vai para o diálogo da extração, então ela diz o problema
    try:
        return generate_candidate_kcs(solutions, statement, llm)
    except InvalidLLMResponseError as exc:
        raise InvalidLLMResponseError(f"problema {problem_id}, {exc}") from exc


class KcGenKtGenerator:
    def __init__(
        self, llm: LLMClient, embed: Callable[[list[str]], np.ndarray] | None = None
    ) -> None:
        self._llm = llm  # o cliente real (ou um falso nos testes); o cache é montado por job
        self._embed = embed or embed_solutions  # o CodeBERT, ou vetores falsos nos testes

    def generate(
        self,
        correct_runs: pd.DataFrame,
        statements: dict[int, str | None],
        classroom_id: int,
        assignment_id: int,
        on_stage: Callable[[str], None],
        on_progress: Callable[[int, int], None],
    ) -> GeneratedKnowledgeComponents:
        cache_dir = data_layout.llm_cache_dir(classroom_id, assignment_id)

        # Ordenado como texto de propósito ("10" antes de "2"), fiel ao TCC 1, não "corrigir".
        problem_ids = sorted(str(p) for p in correct_runs["problem_id"].dropna().unique())

        # Etapas 1-2 por problema, a amostra e os KCs candidatos, com o enunciado quando existe
        on_stage("generate")
        generate_llm = CachedLLMClient(self._llm, cache_dir, stage="generate")
        # A amostragem roda antes e em ordem, só as chamadas ao LLM vão para o paralelo
        generate_tasks = {}
        samples_by_problem: dict[str, list[dict]] = {}
        for problem_id in problem_ids:
            runs = correct_runs[correct_runs["problem_id"].astype(str) == problem_id]
            samples = select_sample_solutions(runs, self._embed)
            samples_by_problem[problem_id] = samples
            generate_tasks[problem_id] = partial(
                _generate_for_problem,
                problem_id,
                [s["code"] for s in samples],
                statements.get(int(problem_id)),
                generate_llm,
            )
        generated = run_in_parallel(generate_tasks, on_progress)
        candidate_kcs_by_problem = {p: generated[p] for p in problem_ids}

        # Etapas 3-4, nomes únicos de KC viram grupos; poucos nomes pulam SBERT e a nomeação.
        unique_names: list[str] = []
        for problem_id in problem_ids:
            for kc in candidate_kcs_by_problem[problem_id]:
                if kc["name"] not in unique_names:
                    unique_names.append(kc["name"])

        on_stage("cluster")
        if len(unique_names) < min(CANDIDATE_GROUP_COUNTS):
            group_of_name = {name: i for i, name in enumerate(unique_names)}
            group_names = {i: name for i, name in enumerate(unique_names)}
            n_groups = len(unique_names)
        else:
            n_groups, group_of_name, group_names = self._group_and_name(
                unique_names, cache_dir, on_progress
            )

        # Etapa 5, a Q-matrix binária problema × grupo.
        on_stage("qmatrix")
        qmatrix = build_qmatrix(
            problem_ids,
            candidate_kcs_by_problem,
            {"n_clusters_selected": n_groups, "kc_to_cluster": group_of_name},
        )
        return GeneratedKnowledgeComponents(
            problem_ids=[int(p) for p in problem_ids],
            group_names=group_names,
            groups_by_problem={
                int(p): [g for g in range(n_groups) if int(qmatrix.loc[p][f"kc_{g}"]) == 1]
                for p in problem_ids
            },
            candidate_kcs={int(p): candidate_kcs_by_problem[p] for p in problem_ids},
            group_of_name=group_of_name,
            sampled_solutions={
                int(p): [int(s["submission_id"]) for s in samples_by_problem[p]]
                for p in problem_ids
            },
            model_id=KC_GENERATION_MODEL_ID,
            prompt_version=PROMPT_VERSION,
        )

    def _group_and_name(
        self,
        unique_names: list[str],
        cache_dir: Path,
        on_progress: Callable[[int, int], None],
    ) -> tuple[int, dict[str, int], dict[int, str]]:
        # SBERT, silhouette/HAC, o LLM nomeia cada grupo; import local, só carrega se for agrupar.
        from sentence_transformers import SentenceTransformer

        embeddings = SentenceTransformer(SBERT_MODEL, revision=SBERT_REVISION).encode(unique_names)
        n_groups, _scores = choose_kc_group_count(embeddings)
        labels = group_similar_kcs(embeddings, n_groups)
        members: dict[int, list[str]] = {}
        for name, group in zip(unique_names, labels):
            members.setdefault(int(group), []).append(name)

        name_llm = CachedLLMClient(self._llm, cache_dir, stage="label")
        named = run_in_parallel(
            {
                group: partial(name_kc_group, members[group], name_llm, group)
                for group in sorted(members)
            },
            on_progress,
        )
        group_of_name: dict[str, int] = {}
        group_names: dict[int, str] = {}
        for group in sorted(members):
            group_names[group] = named[group]["name"]
            for name in members[group]:
                group_of_name[name] = group
        return n_groups, group_of_name, group_names
