# Fixtures dos testes do ml/.

from __future__ import annotations

from pathlib import Path

import pytest
import torch


@pytest.fixture
def cpu_device() -> torch.device:
    # Os testes de caracterização nunca tocam a GPU
    return torch.device("cpu")


@pytest.fixture
def kc_reference_dir() -> Path:
    # Os artefatos reais do KCGen-KT do TCC 1 para o A439
    return Path(__file__).resolve().parents[1] / "data" / "kc"
