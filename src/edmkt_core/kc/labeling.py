# Ported from tcc.edm.kt — notebooks/03b_kc_generation.ipynb cell 15 (cluster labeling, Etapa 4).
# Frozen prompt (D-01) kept verbatim; the inline anthropic call is replaced by the injected
# LLMClient.generate (DIP, KC-01). Markdown-fence parsing dropped from the core primary path.

from __future__ import annotations

from edmkt_core.kc.ports import LLMClient

# Prompt adapted from Duan et al. (2025), Table 9 — cluster labeling stage.
_CLUSTER_LABEL_SYSTEM = (
    "You are an expert CS educator labeling clusters of Knowledge Components (KCs) "
    "for an introductory Java programming course. "
    "A KC is a specific, teachable concept (3-8 words). "
    "Your task: given a cluster of semantically similar KCs, decide whether one KC "
    "already represents the group well, or synthesize a concise new label that captures "
    "the common underlying concept."
)

# Schema for the single-label cluster output (mirrors the cell-15 contract: kc_id/name/reasoning).
CLUSTER_LABEL_SCHEMA: dict = {
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


def label_cluster(cluster_kcs: list[str], llm: LLMClient, cluster_id: int) -> dict:
    """Label one cluster of KCs via the injected LLM port (Duan et al. 2025, Table 9)."""
    result = llm.generate(
        _CLUSTER_LABEL_SYSTEM, _build_label_prompt(cluster_kcs, cluster_id), CLUSTER_LABEL_SCHEMA
    )
    result["kc_id"] = cluster_id  # pin the id regardless of LLM output (cell-15 invariant)
    return result
