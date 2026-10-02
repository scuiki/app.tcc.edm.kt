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

# Roda a suíte rápida, sem os testes regression e literature, que pedem a GPU e o EDMKT_CSEDM_PATH
CMD ["python", "-m", "pytest", "-q"]
