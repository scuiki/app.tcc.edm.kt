#!/usr/bin/env bash
# First live deploy of the EDM·KT app on nitro (Phase 5 E2E).
#
# nitro-env compliance:
#   - single uvicorn worker (state lives in SQLite/FS; never fork web workers)
#   - --gpus all: SBERT (KC-gen) uses the dGPU (NVIDIA Container Toolkit is installed)
#   - --security-opt label=disable: required to read /srv bind mounts under SELinux
#   - -p 127.0.0.1:PORT : loopback-only publish (NEVER a bare port — that leaks on the LAN
#     past firewalld). Use 100.96.0.53 instead to reach it over Tailscale.
#
# Credential (D-01, threat model): the host's verified `claude` binary (2.1.185) and ONLY the
# two OAuth credential files are mounted READ-ONLY — never baked into the image, never via env.
set -euo pipefail

REPO="/srv/dev/studies/app.tcc.edm.kt"
CLAUDE_BIN="/home/leokuntz/.local/share/claude/versions/2.1.185"
PORT="${EDMKT_PORT:-8099}"
BIND_IP="${EDMKT_BIND_IP:-127.0.0.1}"   # 127.0.0.1 = local only; 100.96.0.53 = Tailscale

exec docker run --rm --name edmkt-app \
  --gpus all \
  --security-opt label=disable \
  -p "${BIND_IP}:${PORT}:8099" \
  -v "${REPO}:/app" \
  -v "${CLAUDE_BIN}:/usr/local/bin/claude:ro" \
  -v "/home/leokuntz/.claude/.credentials.json:/root/.claude/.credentials.json:ro" \
  -v "/home/leokuntz/.claude.json:/root/.claude.json:ro" \
  -e EDMKT_KC_CWD=/tmp \
  -e HF_HUB_OFFLINE=1 \
  -e TRANSFORMERS_OFFLINE=1 \
  edmkt-app:dev
