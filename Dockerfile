# Imagem de teste do EDM·KT e base da do app, com a tag fixa que guarda o torch e o numpy
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime

# A ordem dos modificadores Java nos AST paths sai de um set e depende do hash, que o app fixa em 0
ENV PYTHONHASHSEED=0

WORKDIR /app

# Install the package + dev deps. torch already ships in the base image.
COPY pyproject.toml ./
COPY src/api ./src/api
COPY src/ml ./src/ml
COPY tests ./tests
RUN pip install --no-cache-dir -e ".[dev]"

# Os modelos de vetores do KCGen-KT ficam na imagem, na revisão fixada, e o app roda offline
# Sem a conversão automática do transformers, que baixaria pesos de fora da revisão fixada
ENV DISABLE_SAFETENSORS_CONVERSION=1
RUN PYTHONPATH=/app/src python -c "from ml.kc_generation.embedding_models import download_embedding_models; download_embedding_models()"

# Roda a suíte rápida, sem os testes regression e literature, que pedem a GPU e o EDMKT_CSEDM_PATH
CMD ["python", "-m", "pytest", "-q"]
