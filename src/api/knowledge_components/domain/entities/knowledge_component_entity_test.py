# O marcador de gerado do conceito, pelo nome gerado e pela data da última edição.
from __future__ import annotations

from api.knowledge_components.domain.entities.knowledge_component_entity import KnowledgeComponent


def _kc(generated_name: str | None, updated_at: str | None) -> KnowledgeComponent:
    return KnowledgeComponent(
        id=1, assignment_id=1, name="Laços", generated_name=generated_name, updated_at=updated_at
    )


def test_only_a_generated_concept_that_nobody_edited_is_generated_by_the_llm():
    assert _kc("loops", None).is_generated_by_llm is True
    # Renomeado pelo professor, o nome passa a ser dele
    assert _kc("loops", "2026-10-08T12:00:00+00:00").is_generated_by_llm is False
    # Criado pelo professor, sem nome gerado
    assert _kc(None, None).is_generated_by_llm is False
    assert _kc(None, "2026-10-08T12:00:00+00:00").is_generated_by_llm is False


def test_a_new_concept_starts_without_an_edit():
    assert KnowledgeComponent(id=None, assignment_id=1, name="Laços").updated_at is None
