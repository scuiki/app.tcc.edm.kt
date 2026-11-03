# A imagem de teste, com a base fixada pelo digest, que guarda o torch e o numpy
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime@sha256:c16f4c749e2d9e96878875cdf6cc45cddda1d1a36fddd371dd6f2360f1b6e2a2 AS core

# A ordem dos modificadores Java nos AST paths sai de um set e depende do hash, que o app fixa em 0
ENV PYTHONHASHSEED=0

WORKDIR /app

# O pacote e as dependências de dev, nas versões do requirements.lock, e o torch já vem da base
COPY pyproject.toml requirements.lock ./
COPY src/api ./src/api
COPY src/ml ./src/ml
COPY tests ./tests
RUN pip install --no-cache-dir -c requirements.lock -e ".[dev]"

# Os modelos de vetores do KCGen-KT ficam na imagem, na revisão fixada, e o app roda offline
# Sem a conversão automática do transformers, que baixaria pesos de fora da revisão fixada
ENV DISABLE_SAFETENSORS_CONVERSION=1
RUN PYTHONPATH=/app/src python -c "from ml.kc_generation.embedding_models import download_embedding_models; download_embedding_models()"

# Roda a suíte rápida, sem os testes regression e literature, que pedem a GPU e o EDMKT_CSEDM_PATH
CMD ["python", "-m", "pytest", "-q"]

# A imagem do app, que herda o PYTHONHASHSEED=0 e os modelos de vetores da de teste
FROM core AS app

# O ml/ e o api/ são importados de src/, porque a instalação editável é anterior ao bind mount
ENV PYTHONPATH=/app/src

# O CLI do Claude da geração de KCs, na versão fixada e conferido pelo checksum do manifesto oficial
ADD --checksum=sha256:eb224419e344575faa4a1f39b290b649425a10cd5ee2ef1d003480cd9ae57eb0 --chmod=755 https://downloads.claude.ai/claude-code-releases/2.1.317/linux-x64/claude /usr/local/bin/claude

# Sem atualização automática, para o CLI ficar na versão fixada
ENV DISABLE_AUTOUPDATER=1

# O 0.0.0.0 é de dentro do container, e a api não publica porta no compose
EXPOSE 8099
CMD ["uvicorn", "api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8099", "--workers", "1"]
