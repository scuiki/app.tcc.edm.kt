# Os modelos de vetores do KCGen-KT, na revisão fixada do Hugging Face, para os vetores não mudarem.

from __future__ import annotations

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
