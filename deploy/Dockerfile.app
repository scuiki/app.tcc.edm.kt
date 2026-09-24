# Runtime image for the EDM·KT FastAPI app + KC pipeline (Phase 5 first live deploy).
# Derives FROM the CORE-03 reproducibility anchor (edmkt-core:dev) so the regression-test numerics
# image stays pure: this layer only ADDS a runtime concern — the pre-baked SBERT model.
# The `claude` CLI (D-01 subscription transport) and the OAuth credential are deliberately NOT
# baked: they are mounted read-only at run time (see run-app.sh). That pins the host's verified
# CLI version (2.1.185) and keeps the secret out of the image layers (threat model: no credential
# in env, no credential in image).
FROM edmkt-core:dev

# Pre-bake the SBERT model so KC-gen never downloads at run time (offline reliability on nitro).
# all-MiniLM-L6-v2 is the frozen KCGen-KT embedding model (science pin, mirrors TCC 1).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Container binds 0.0.0.0; the host-side `-p 127.0.0.1:PORT` bind in run-app.sh is the real
# network gate (nitro-env: never publish a bare port — loopback publish = local-only).
# ml/ e api/ são importados de src/ (a instalação editável da imagem base é anterior a eles).
ENV PYTHONPATH=/app/src

EXPOSE 8099
CMD ["uvicorn", "api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8099", "--workers", "1"]
