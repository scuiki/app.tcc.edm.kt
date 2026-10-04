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
from ml.kc_generation.embedding_models import embed_kc_names, embed_solutions
from ml.kc_generation.group_naming import name_kc_group
from ml.kc_generation.kc_grouping import group_similar_kcs, kc_group_count
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
    problem_id: int, solutions: list[str], statement: str | None, llm: LLMClient
) -> list[dict[str, str]]:
    # A mensagem da resposta inválida vai para o diálogo da extração, então ela diz o problema
    try:
        return generate_candidate_kcs(solutions, statement, llm)
    except InvalidLLMResponseError as exc:
        raise InvalidLLMResponseError(f"problema {problem_id}, {exc}") from exc


def _name_group(names: list[str], llm: LLMClient) -> str:
    # A mensagem da resposta inválida vai para o diálogo da extração, então ela diz o grupo
    try:
        return name_kc_group(names, llm)
    except InvalidLLMResponseError as exc:
        raise InvalidLLMResponseError(f"grupo {names}, {exc}") from exc


class KcGenKtGenerator:
    def __init__(
        self,
        llm: LLMClient,
        embed: Callable[[list[str]], np.ndarray] | None = None,
        embed_names: Callable[[list[str]], np.ndarray] | None = None,
    ) -> None:
        self._llm = llm  # o cliente real (ou um falso nos testes); o cache é montado por job
        self._embed = embed or embed_solutions  # o CodeBERT, ou vetores falsos nos testes
        self._embed_names = embed_names or embed_kc_names  # o SBERT, ou vetores falsos nos testes

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

        # Os problemas em ordem numérica, a ordem em que os nomes de KC entram no agrupamento
        problem_ids = sorted(int(p) for p in correct_runs["problem_id"].dropna().unique())

        # Etapas 1-2 por problema, a amostra e os KCs candidatos, com o enunciado quando existe
        on_stage("generate")
        generate_llm = CachedLLMClient(self._llm, cache_dir, stage="generate")
        # A amostragem roda antes e em ordem, só as chamadas ao LLM vão para o paralelo
        generate_tasks = {}
        samples_by_problem: dict[int, list[dict]] = {}
        for problem_id in problem_ids:
            runs = correct_runs[correct_runs["problem_id"] == problem_id]
            samples = select_sample_solutions(runs, self._embed)
            samples_by_problem[problem_id] = samples
            generate_tasks[problem_id] = partial(
                _generate_for_problem,
                problem_id,
                [s["code"] for s in samples],
                statements.get(problem_id),
                generate_llm,
            )
        generated = run_in_parallel(generate_tasks, on_progress)
        candidate_kcs_by_problem = {p: generated[p] for p in problem_ids}

        # Etapas 3-4, os nomes únicos, na ordem dos problemas e das respostas, viram conceitos
        on_stage("cluster")
        unique_names = list(
            dict.fromkeys(kc["name"] for p in problem_ids for kc in candidate_kcs_by_problem[p])
        )
        concept_names, concept_of_name = self._group_and_name(unique_names, cache_dir, on_progress)

        # Etapa 5, a Q-matrix binária problema × conceito.
        on_stage("qmatrix")
        qmatrix = build_qmatrix(
            problem_ids,
            candidate_kcs_by_problem,
            {"n_clusters_selected": len(concept_names), "kc_to_cluster": concept_of_name},
        )
        return GeneratedKnowledgeComponents(
            problem_ids=problem_ids,
            group_names=dict(enumerate(concept_names)),
            groups_by_problem={
                p: [g for g in range(len(concept_names)) if int(qmatrix.loc[p][f"kc_{g}"]) == 1]
                for p in problem_ids
            },
            candidate_kcs=candidate_kcs_by_problem,
            group_of_name=concept_of_name,
            sampled_solutions={
                p: [int(s["submission_id"]) for s in samples_by_problem[p]] for p in problem_ids
            },
            model_id=KC_GENERATION_MODEL_ID,
            prompt_version=PROMPT_VERSION,
        )

    def _group_and_name(
        self,
        unique_names: list[str],
        cache_dir: Path,
        on_progress: Callable[[int, int], None],
    ) -> tuple[list[str], dict[str, int]]:
        # SBERT e HAC no número de grupos do paper, e o LLM nomeia os grupos com mais de um KC
        if not unique_names:
            return [], {}
        labels = group_similar_kcs(
            self._embed_names(unique_names), kc_group_count(len(unique_names))
        )
        members: dict[int, list[str]] = {}
        for name, label in zip(unique_names, labels):
            members.setdefault(int(label), []).append(name)

        name_llm = CachedLLMClient(self._llm, cache_dir, stage="label")
        tasks = {
            group: partial(_name_group, names, name_llm)
            for group, names in sorted(members.items())
            if len(names) > 1
        }
        # Sem grupo de mais de um KC, a nomeação não tem itens e o progresso fica vazio
        named = run_in_parallel(tasks, on_progress) if tasks else {}
        # O grupo de um KC só fica com o nome dele, em minúsculas como os nomes que o LLM dá
        group_name = {
            group: named[group] if group in named else names[0].lower()
            for group, names in sorted(members.items())
        }
        # Os grupos com o mesmo nome viram um conceito só, na ordem dos grupos
        concept_names = list(dict.fromkeys(group_name.values()))
        concept_of_name = {
            name: concept_names.index(group_name[group])
            for group, names in members.items()
            for name in names
        }
        return concept_names, concept_of_name
