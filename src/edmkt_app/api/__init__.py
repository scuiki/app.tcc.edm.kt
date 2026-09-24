"""Camada HTTP do EDM·KT — primeira superfície de rede do projeto (D-12).

Composição: `create_app()` (app.py) é a raiz que monta os routers de treino e ingestão
sobre as portas já prontas das Fases 2-3. `ml` segue framework-free; o HTTP só
marshalla request↔serviço, nunca treina nem reimplementa lock/commit.
"""

from __future__ import annotations

from edmkt_app.api.app import create_app

__all__ = ["create_app"]
