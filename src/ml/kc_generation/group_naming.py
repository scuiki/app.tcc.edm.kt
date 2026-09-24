# Etapa 4 do KCGen-KT, pede ao LLM um nome por grupo de KCs; prompt congelado, é chave do cache.

from __future__ import annotations

from ml.kc_generation.llm_client import LLMClient

# Prompt adaptado de Duan et al. (2025), Tabela 9, etapa de rotulagem de clusters.
_CLUSTER_LABEL_SYSTEM = (
    "You are an expert CS educator labeling clusters of Knowledge Components (KCs) "
    "for an introductory Java programming course. "
    "A KC is a specific, teachable concept (3-8 words). "
    "Your task: given a cluster of semantically similar KCs, decide whether one KC "
    "already represents the group well, or synthesize a concise new label that captures "
    "the common underlying concept."
)

# Schema da saída de um label por cluster (espelha o contrato da célula 15, kc_id/name/reasoning).
KC_GROUP_NAME_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "kc_id": {"type": "integer"},
        "name": {"type": "string"},
        "reasoning": {"type": "string"},
    },
    "required": ["name", "reasoning"],
}


def _build_label_prompt(cluster_kcs: list[str], cluster_id: int) -> str:
    kc_list = "\n".join(f"- {kc}" for kc in cluster_kcs)
    return (
        "You are labeling a cluster of related Knowledge Components for a programming course.\n\n"
        "The following KCs were grouped together based on semantic similarity:\n"
        f"{kc_list}\n\n"
        "Decide: does one of these KCs already represent the entire cluster well, "
        "or should you synthesize a new label that captures the common underlying concept?\n\n"
        f"Respond ONLY with a valid JSON object (cluster_id = {cluster_id}):\n"
        "{\n"
        f'  "kc_id": {cluster_id},\n'
        '  "name": "Final KC label (3-8 words)",\n'
        '  "reasoning": "Why this label represents the cluster (1 sentence)"\n'
        "}"
    )


def name_kc_group(cluster_kcs: list[str], llm: LLMClient, cluster_id: int) -> dict:
    # Rotula um cluster de KCs via a porta do LLM injetada (Duan et al. 2025, Tabela 9).
    result = llm.generate(
        _CLUSTER_LABEL_SYSTEM, _build_label_prompt(cluster_kcs, cluster_id), KC_GROUP_NAME_SCHEMA
    )
    result["kc_id"] = cluster_id  # fixa o id independente da saída do LLM (invariante da célula 15)
    return result
