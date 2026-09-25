# IKnowledgeComponentGenerator sobre o KCGen-KT, amostra, gera, agrupa/nomeia, Q-matrix.
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Callable, Hashable, TypeVar

import pandas as pd

from api.knowledge_components.domain.interfaces.knowledge_component_generator import (
    GeneratedKnowledgeComponents,
)
from api.knowledge_components.infrastructure.implementations.llm_response_cache import (
    CachedLLMClient,
)
from api.shared.infrastructure.filesystem import data_layout
from ml.kc_generation.candidate_generation import generate_candidate_kcs
from ml.kc_generation.group_naming import name_kc_group
from ml.kc_generation.kc_grouping import (
    CANDIDATE_GROUP_COUNTS,
    choose_kc_group_count,
    group_similar_kcs,
)
from ml.kc_generation.llm_client import LLMClient
from ml.kc_generation.qmatrix_builder import build_qmatrix
from ml.kc_generation.solution_sampling import select_sample_solutions

SBERT_MODEL = "all-MiniLM-L6-v2"  # o modelo de embedding congelado do KCGen-KT (TCC 1)

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


class KcGenKtGenerator:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm  # o cliente real (ou um falso nos testes); o cache é montado por job

    def generate(
        self,
        cleaned_submissions: pd.DataFrame,
        classroom_id: int,
        assignment_id: int,
        on_stage: Callable[[str], None],
        on_progress: Callable[[int, int], None],
    ) -> GeneratedKnowledgeComponents:
        cache_dir = data_layout.llm_cache_dir(classroom_id, assignment_id)

        # O KCGen-KT vê só código correto, mostrar código errado ao LLM ensinaria o KC errado.
        correct = cleaned_submissions[cleaned_submissions["is_correct"] == 1]
        # Ordenado como texto de propósito ("10" antes de "2"), fiel ao TCC 1, não "corrigir".
        problem_ids = sorted(str(p) for p in correct["problem_id"].dropna().unique())

        # Etapas 1-2 por problema, amostra diversa e KCs candidatos pelo LLM, sem KC é erro duro.
        on_stage("generate")
        generate_llm = CachedLLMClient(self._llm, cache_dir, stage="generate")
        # A amostragem roda antes e em ordem, só as chamadas ao LLM vão para o paralelo
        generate_tasks = {}
        for problem_id in problem_ids:
            solutions = correct[correct["problem_id"].astype(str) == problem_id]
            samples = select_sample_solutions(solutions, n=5)
            generate_tasks[problem_id] = partial(
                generate_candidate_kcs, int(problem_id), [s["code"] for s in samples], generate_llm
            )
        generated = run_in_parallel(generate_tasks, on_progress)
        candidate_kcs_by_problem: dict = {p: generated[p] for p in problem_ids}

        # Etapas 3-4, nomes únicos de KC viram grupos; poucos nomes pulam SBERT e a nomeação.
        unique_names: list[str] = []
        for problem_id in problem_ids:
            for kc in candidate_kcs_by_problem[problem_id]["kcs"]:
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
            problem_descriptions={
                int(p): candidate_kcs_by_problem[p]["problem_description"]
                for p in problem_ids
                if candidate_kcs_by_problem[p].get("problem_description")
            },
        )

    def _group_and_name(
        self,
        unique_names: list[str],
        cache_dir: Path,
        on_progress: Callable[[int, int], None],
    ) -> tuple[int, dict[str, int], dict[int, str]]:
        # SBERT, silhouette/HAC, o LLM nomeia cada grupo; import local, só carrega se for agrupar.
        from sentence_transformers import SentenceTransformer

        embeddings = SentenceTransformer(SBERT_MODEL).encode(unique_names)
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
