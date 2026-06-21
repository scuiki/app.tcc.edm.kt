"""Testes RED de recomendações (REC-01) — ranking puro, sem LLM, sem fixture de modelo.

Pinam o contrato de `edmkt_app.recommendations` antes de existir (Wave 0): as recomendações
de reforço rankeiam os KCs de MENOR mastery média da turma primeiro (reaproveitando a lógica
de KCs críticos), e emitem um texto-modelo em pt-BR — sem chamada de LLM (D-07: ranking puro).
Falham agora com ImportError em `edmkt_app.recommendations`.
"""

from __future__ import annotations


def test_recommendations_rank_lowest_mastery_first():
    # REC-01: KC de menor mastery média da turma vem primeiro na lista de reforço.
    from edmkt_app.recommendations import recommend_reinforcement

    # (kc_id, kc_name, mean_mastery) — KC 'Laços' (0.15) é o mais fraco, 'Strings' (0.85) o mais forte.
    kc_means = [
        (10, "Laços", 0.15),
        (20, "Condicionais", 0.50),
        (30, "Strings", 0.85),
    ]
    recs = recommend_reinforcement(kc_means)

    # os KCs aparecem do mais fraco ao mais forte (ascendente por mastery).
    ordered_names = [r["kc_name"] for r in recs]
    assert ordered_names == ["Laços", "Condicionais", "Strings"]
    # cada recomendação carrega um texto pt-BR não-vazio mencionando o KC.
    top = recs[0]
    assert top["kc_id"] == 10
    assert "Laços" in top["text"]
    assert top["text"].strip() != ""


def test_recommendations_empty_when_no_kcs():
    # Sem KCs (turma sem Q-matrix aprovada) → lista vazia, sem erro.
    from edmkt_app.recommendations import recommend_reinforcement

    assert recommend_reinforcement([]) == []
