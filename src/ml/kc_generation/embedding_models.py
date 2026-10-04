# Os modelos de vetores do KCGen-KT, na revisão fixada do Hugging Face, para os vetores não mudarem.

from __future__ import annotations

from functools import lru_cache

import numpy as np

# O CodeBERT do paper, para os vetores das soluções corretas
CODEBERT_MODEL = "microsoft/codebert-base"
CODEBERT_REVISION = "3b0952feddeffad0063f274080e3c23d75e7eb39"

# O SBERT do repositório oficial, para os vetores dos nomes de KC
SBERT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SBERT_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def download_embedding_models() -> None:
    # Põe os dois modelos no cache do Hugging Face, chamado no build da imagem e nunca no app
    from sentence_transformers import SentenceTransformer
    from transformers import AutoModel, AutoTokenizer

    AutoTokenizer.from_pretrained(CODEBERT_MODEL, revision=CODEBERT_REVISION)
    AutoModel.from_pretrained(CODEBERT_MODEL, revision=CODEBERT_REVISION)
    SentenceTransformer(SBERT_MODEL, revision=SBERT_REVISION)


# As soluções entram no CodeBERT de 32 em 32, e o lote é fixo porque os vetores mudam com ele
SOLUTION_EMBEDDING_BATCH_SIZE = 32

# O tokenizador do CodeBERT corta a solução nos 512 tokens que o modelo aceita
_MAX_TOKENS = 512


@lru_cache(maxsize=1)
def _codebert():
    # Carrega o CodeBERT uma vez por processo, na GPU quando ela existe
    import torch
    from transformers import AutoModel, AutoTokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    tokenizer = AutoTokenizer.from_pretrained(CODEBERT_MODEL, revision=CODEBERT_REVISION)
    model = AutoModel.from_pretrained(CODEBERT_MODEL, revision=CODEBERT_REVISION)
    return tokenizer, model.to(device).eval(), device


def embed_solutions(codes: list[str]) -> np.ndarray:
    # A média da última camada pela máscara de atenção, com norma 1, como o repositório do Duan
    import torch

    tokenizer, model, device = _codebert()
    vectors = []
    with torch.no_grad():
        for start in range(0, len(codes), SOLUTION_EMBEDDING_BATCH_SIZE):
            batch = tokenizer(
                codes[start : start + SOLUTION_EMBEDDING_BATCH_SIZE],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=_MAX_TOKENS,
            ).to(device)
            hidden = model(**batch).last_hidden_state
            mask = batch["attention_mask"].unsqueeze(-1).to(hidden.dtype)
            mean = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1e-9)
            vectors.append(torch.nn.functional.normalize(mean, dim=1).cpu())
    return torch.cat(vectors).numpy()
