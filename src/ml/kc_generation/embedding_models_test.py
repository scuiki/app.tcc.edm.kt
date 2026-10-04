# As revisões fixadas dos modelos de vetores e o download deles no build da imagem base.

import re
from pathlib import Path

from ml.kc_generation import embedding_models

_ROOT = Path(__file__).resolve().parents[3]


def test_the_revisions_are_full_commit_hashes():
    # Um nome de branch como "main" mudaria os vetores quando o Hugging Face publicasse outra versão
    for revision in (embedding_models.CODEBERT_REVISION, embedding_models.SBERT_REVISION):
        assert re.fullmatch(r"[0-9a-f]{40}", revision)


def test_the_base_image_downloads_the_models_at_build_time():
    dockerfile = (_ROOT / "Dockerfile").read_text()
    assert "download_embedding_models()" in dockerfile
