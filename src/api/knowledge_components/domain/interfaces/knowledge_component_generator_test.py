# GeneratedKnowledgeComponents, uma geração com um problema sem KC não pode ser gravada.
from __future__ import annotations

import pytest

from api.knowledge_components.domain.interfaces.knowledge_component_generator import (
    GeneratedKnowledgeComponents,
    ProblemWithoutKnowledgeComponent,
)


def test_every_problem_with_a_kc_passes():
    generated = GeneratedKnowledgeComponents(
        problem_ids=[1, 2],
        group_names={0: "loops"},
        groups_by_problem={1: [0], 2: [0]},
        translated_group_names={0: "Laços"},
    )

    generated.ensure_every_problem_has_a_kc()


def test_a_problem_without_kc_fails_the_whole_generation():
    generated = GeneratedKnowledgeComponents(
        problem_ids=[1, 2],
        group_names={0: "loops"},
        groups_by_problem={1: [0], 2: []},
        translated_group_names={0: "Laços"},
    )

    with pytest.raises(ProblemWithoutKnowledgeComponent, match="problema 2"):
        generated.ensure_every_problem_has_a_kc()


def test_an_empty_generation_fails():
    generated = GeneratedKnowledgeComponents(
        problem_ids=[], group_names={}, groups_by_problem={}, translated_group_names={}
    )

    with pytest.raises(ProblemWithoutKnowledgeComponent, match="nenhum problema correto gerou KCs"):
        generated.ensure_every_problem_has_a_kc()
