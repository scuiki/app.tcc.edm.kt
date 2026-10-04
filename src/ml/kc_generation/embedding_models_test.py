# As revisões fixadas dos modelos de vetores e o download deles no build da imagem base.

import re
from pathlib import Path

import numpy as np
import pytest

from ml.kc_generation import embedding_models

_ROOT = Path(__file__).resolve().parents[3]


def test_the_revisions_are_full_commit_hashes():
    # Um nome de branch como "main" mudaria os vetores quando o Hugging Face publicasse outra versão
    for revision in (embedding_models.CODEBERT_REVISION, embedding_models.SBERT_REVISION):
        assert re.fullmatch(r"[0-9a-f]{40}", revision)


def test_the_base_image_downloads_the_models_at_build_time():
    dockerfile = (_ROOT / "Dockerfile").read_text()
    assert "download_embedding_models()" in dockerfile


@pytest.mark.regression
def test_codebert_gives_unit_vectors_and_the_same_vector_for_the_same_code():
    # Carrega o CodeBERT de verdade, por isso fica fora da suíte padrão
    codes = [
        "public int f() { return 1; }",
        "public int f() { return 1; }",
        "public boolean g(int n) { return n > 0; }",
    ]
    vectors = embedding_models.embed_solutions(codes)
    assert vectors.shape == (3, 768)
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5)
    assert np.array_equal(vectors[0], vectors[1])
    assert not np.allclose(vectors[0], vectors[2])


@pytest.mark.regression
def test_codebert_vectors_are_the_masked_mean_of_the_last_layer_cut_at_512_tokens():
    # O cálculo à mão, uma solução por vez e sem padding, contra o lote do app
    import torch
    from transformers import AutoModel, AutoTokenizer

    model_name = embedding_models.CODEBERT_MODEL
    revision = embedding_models.CODEBERT_REVISION
    tokenizer = AutoTokenizer.from_pretrained(model_name, revision=revision)
    model = AutoModel.from_pretrained(model_name, revision=revision).eval()
    short = "public int f() { return 1; }"
    # A longa passa de 512 tokens, e no mesmo lote a curta recebe padding
    long = "int x = 0;\n" * 300
    assert len(tokenizer(long)["input_ids"]) > 512

    def by_hand(code: str) -> np.ndarray:
        batch = tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
        with torch.no_grad():
            hidden = model(**batch).last_hidden_state[0]
        return torch.nn.functional.normalize(hidden.mean(dim=0), dim=0).numpy()

    vectors = embedding_models.embed_solutions([short, long])

    for code, vector in zip([short, long], vectors):
        assert np.allclose(vector, by_hand(code), atol=1e-4)
