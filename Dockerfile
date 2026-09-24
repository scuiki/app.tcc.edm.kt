# EDM·KT dev/test image (ml/ + api/).
# Base on the PyTorch CUDA runtime (CLAUDE.md containerization guidance).
# FIXED TAG (no `latest`) — this image IS the reproducibility anchor (CORE-03): its conda
# env ships torch==2.7.1+cu128 / numpy==2.2.6, the versions the regression test validated
# (A439 first-attempt AUC = 0.7608, in band [0.7027, 0.7627]). nitro GPU is an RTX 4050
# (Ada, sm_89), covered by the cu128 wheels. requirements.lock records the resolved env.
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime

WORKDIR /app

# Install the package + dev deps. torch already ships in the base image.
COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
RUN pip install --no-cache-dir -e ".[dev]"

# Default: run the quick suite (regression test deselected; needs EDMKT_CSEDM_PATH).
CMD ["python", "-m", "pytest", "-q"]
