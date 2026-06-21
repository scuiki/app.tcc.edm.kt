"""Router de treino — POST dispara o subprocess, GET faz poll do progresso (MODEL-01/02).

Esqueleto na Task 1; as rotas chegam na Task 2.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["training"])
