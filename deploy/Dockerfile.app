# Runtime image for the EDM·KT FastAPI app + KC pipeline (Phase 5 first live deploy).
# Derives FROM the CORE-03 reproducibility anchor (edmkt-core:dev), which already carries the
# KCGen-KT embedding models (CodeBERT and SBERT) at their pinned revisions.
# The `claude` CLI (D-01 subscription transport) and the OAuth credential are deliberately NOT
# baked: they are mounted read-only at run time (see docker-compose.yml). The mount follows the
# host's current CLI version and keeps the secret out of the image layers (threat model: no
# credential in env, no credential in image).
FROM edmkt-core:dev

# O PYTHONHASHSEED=0 vem da imagem base e não pode mudar, porque a ordem dos AST paths depende dele

# Container binds 0.0.0.0; the host-side `-p 127.0.0.1:PORT` bind in run-app.sh is the real
# network gate (nitro-env: never publish a bare port — loopback publish = local-only).
# ml/ e api/ são importados de src/ (a instalação editável da imagem base é anterior a eles).
ENV PYTHONPATH=/app/src

EXPOSE 8099
CMD ["uvicorn", "api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8099", "--workers", "1"]
