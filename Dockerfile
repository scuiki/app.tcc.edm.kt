# edmkt_core dev/test image.
# Base on the PyTorch CUDA runtime (CLAUDE.md containerization guidance).
# TODO(plan 06): pin the exact tag to the resolved TCC 1 torch line (e.g.
#   pytorch/pytorch:2.7.x-cuda12.8-cudnn9-runtime). nitro GPU is an RTX 4050
#   (Ada, sm_89) — any cu12x line works; the golden-run is the version oracle.
FROM pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime

WORKDIR /app

# Install the package + dev deps. torch already ships in the base image.
COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
RUN pip install --no-cache-dir -e ".[dev]"

# Default: run the quick suite (golden-run deselected; needs EDMKT_CSEDM_PATH).
CMD ["python", "-m", "pytest", "tests/", "-m", "not golden", "-q"]
