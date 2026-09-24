"""KnowledgeComponentGenerator sobre o KCGen-KT do ml/: amostra → gera → agrupa/nomeia → Q-matrix.

As etapas, a ordem e os dados de entrada de cada uma são os do TCC 1; mudar qualquer um muda os
KCs. Em particular os problemas são ordenados COMO TEXTO ("10" antes de "2"): essa ordem define a
ordem dos nomes de KC que entram no SBERT e, portanto, os grupos.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import pandas as pd

from api.assignments.domain.classroom_slug import ClassroomSlug
from api.assignments.domain.progsnap_assignment_id import ProgSnapAssignmentId
from api.knowledge_components.domain.knowledge_component_generator import (
    GeneratedKnowledgeComponents,
)
from api.knowledge_components.infrastructure.llm_response_cache import CachedLLMClient
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


class KcGenKtGenerator:
    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm  # o cliente real (ou um falso nos testes); o cache é montado por job

    def generate(
        self,
        cleaned_submissions: pd.DataFrame,
        classroom_slug: ClassroomSlug,
        progsnap_assignment_id: ProgSnapAssignmentId,
        on_stage: Callable[[str], None],
    ) -> GeneratedKnowledgeComponents:
        cache_dir = data_layout.llm_cache_dir(classroom_slug, progsnap_assignment_id)

        # O KCGen-KT vê só código CORRETO: mostrar código errado ao LLM ensinaria o KC errado.
        correct = cleaned_submissions[cleaned_submissions["is_correct"] == 1]
        problem_ids = sorted(str(p) for p in correct["problem_id"].dropna().unique())

        # Etapas 1-2 (por problema): amostra diversa → KCs candidatos pelo LLM. Um problema sem
        # nenhum KC levanta NoCandidateKCsError: o job inteiro falha.
        on_stage("generate")
        generate_llm = CachedLLMClient(self._llm, cache_dir, stage="generate")
        candidate_kcs_by_problem: dict = {}
        for problem_id in problem_ids:
            solutions = correct[correct["problem_id"].astype(str) == problem_id]
            samples = select_sample_solutions(solutions, n=5)
            candidate_kcs_by_problem[problem_id] = generate_candidate_kcs(
                int(problem_id), [s["code"] for s in samples], generate_llm
            )

        # Etapas 3-4: nomes únicos de KC → grupos. Com menos nomes únicos que o MENOR candidato
        # de número de grupos, o silhouette não se aplica: cada nome vira o próprio grupo, sem
        # SBERT e sem chamada de nomeação (o caminho real das turmas pequenas).
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
            n_groups, group_of_name, group_names = self._group_and_name(unique_names, cache_dir)

        # Etapa 5: a Q-matrix binária problema × grupo.
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
        )

    def _group_and_name(
        self, unique_names: list[str], cache_dir: Path
    ) -> tuple[int, dict[str, int], dict[int, str]]:
        """SBERT → silhouette/HAC → o LLM nomeia cada grupo. Devolve (n, grupo por nome, nomes).

        O SBERT é importado só aqui: só é carregado quando há nomes suficientes para agrupar.
        """
        from sentence_transformers import SentenceTransformer

        embeddings = SentenceTransformer(SBERT_MODEL).encode(unique_names)
        n_groups, _scores = choose_kc_group_count(embeddings)
        labels = group_similar_kcs(embeddings, n_groups)
        members: dict[int, list[str]] = {}
        for name, group in zip(unique_names, labels):
            members.setdefault(int(group), []).append(name)

        name_llm = CachedLLMClient(self._llm, cache_dir, stage="label")
        group_of_name: dict[str, int] = {}
        group_names: dict[int, str] = {}
        for group in sorted(members):
            group_names[group] = name_kc_group(members[group], name_llm, group)["name"]
            for name in members[group]:
                group_of_name[name] = group
        return n_groups, group_of_name, group_names
