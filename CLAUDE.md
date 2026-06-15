<!-- GSD:project-start source:PROJECT.md -->

## Project

**EDM·KT — Ferramenta Docente (TCC 2)**

Aplicação web docente que aplica *knowledge tracing* a dados de programação introdutória
(formato ProgSnap2) para mostrar ao professor, **durante a disciplina**, o estágio de
domínio da turma por *Knowledge Component* (KC). O professor sobe os dados da própria
turma, o app extrai/valida KCs, treina um modelo **Code-DKT** sobre aquele dado e
apresenta um dashboard de *mastery* por aluno × KC, destacando KCs críticos e alunos em
atenção — fechando com recomendações de reforço.

É a **fase de Implantação (Deployment)** do processo EDM iniciado no TCC 1 (pesquisa em
`../tcc.edm.kt`), que comparou BKT, DKT e Code-DKT e elegeu o Code-DKT como modelo base.

**Core Value:** O professor consegue enxergar **quais conceitos a turma ainda não domina** (mastery por
KC, em dados reais da própria turma) a tempo de ajustar suas aulas. Se tudo o mais falhar,
isto precisa funcionar: dados → KCs → Code-DKT treinado → dashboard de mastery.

### Constraints

- **Tech stack**: backend **Python/FastAPI** (API JSON) obrigatório — reuso de Code-DKT/javalang
  (PyTorch, pyBKT) embrulhado na biblioteca `edmkt_core`. Frontend **React SPA (Vite + TS)**,
  gráficos via `react-chartjs-2`. Persistência SQLite + filesystem. Treino em processo de
  background com **trava global de pipeline** (sem fila durável/Redis).

- **Runtime**: hospedado no servidor **nitro** (Fedora) via **Docker**, com **GPU** disponível
  para treino do Code-DKT; acesso via browser/Tailscale. Seguir convenções do skill `nitro-env`
  ao planejar Docker, portas, firewall e GPU.

- **Reprodutibilidade científica** (Code-DKT, fiel a Shi et al. 2022, não alterar):
  R=50 paths, max_path_length=8, max_path_width=2, embeddings 100-dim → 300-dim,
  LSTM hidden_dim=128, dropout=0.1, Adam lr=5e-4, 40 épocas, batch=128, grad clip=10, seed=42.
  Métrica primária: first-attempt AUC.

- **Entrada**: ProgSnap2 v6 (CodeStateID → snapshot de código Java + Score ∈ [0,1];
  ground-truth binário = Score == 1.0). KC inicial via KCGen-KT validado pelo professor.

- **Performance**: treino é por-assignment e roda em minutos na GPU; a UX precisa contemplar
  uma etapa de treino (não-instantânea) entre upload e dashboard.

- **Sem prazo rígido**: priorizar qualidade e fidelidade científica sobre velocidade.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## TL;DR Recommendation

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11.x (3.10–3.12 OK) | Backend language | Mandatory constraint (reuses `code_dkt.py`, `code_features.py`, javalang, PyTorch, pyBKT). 3.11 is the sweet spot for PyTorch CUDA wheels + FastAPI in 2026. Match whatever the TCC 1 env already uses. |
| FastAPI | 0.137.x (latest 2026) | Web framework / HTTP API | Async-native (so long ML jobs never block the event loop when dispatched to a worker), first-class Pydantic validation for ProgSnap2/Q-matrix payloads, trivial Jinja2 + file-upload support, and it cleanly serves both HTML (HTMX) and JSON. Best fit for "long-running jobs + a dashboard" in Python. |
| Uvicorn | 0.34.x (with `[standard]`) | ASGI server | Reference ASGI server for FastAPI; single-instance, run with `--workers 1` (state lives in SQLite/FS, GPU is shared — do not fork web workers). |
| Jinja2 | 3.1.x | Server-side templating | Renders the 6 prototype pages server-side. The prototype is already plain HTML/Tailwind — porting it to Jinja partials is hours, not weeks. |
| HTMX | 2.0.x (stable; avoid 4.0 beta) | Progressive interactivity | Gives SPA-like UX (poll training status, swap in dashboard fragments, submit KC-validation forms) without a JS build toolchain or a separate frontend repo. Perfect for a Python-only team and a TCC scope. Pin **2.0.x**; 4.0 is still beta in mid-2026. |
| PyTorch | 2.7.x+ on CUDA 12.8 (cu128) | Code-DKT training/inference | Already the TCC 1 dependency. 2.7+ ships prebuilt cu128 wheels with Blackwell/RTX-50xx support; if nitro's GPU is older (Ampere/Ada), any 2.x cu12x line works. **Pin to the exact version TCC 1 trained with** to preserve scientific reproducibility (seed=42, identical numerics). |
| SQLite | 3.x (stdlib `sqlite3`) | Metadata + per-class state store | Single-instance, single-writer, embedded — exactly the right database for one professor's tool. Stores classes, assignments, KC definitions, Q-matrix, job status, training runs. Zero ops, single file, trivially backed up. |
| Redis | 7.2.x / Valkey 7.2 | Job broker for RQ | Lightweight queue + result backend for the single training worker. One small container. |
| RQ (Redis Queue) | 2.x | Background job runner | Runs the live Code-DKT training out-of-process. See "Job execution" below for why RQ over Celery/Dramatiq/BackgroundTasks. |
| anthropic | 0.107.x (latest 2026) | Claude SDK for KCGen-KT | Official SDK. Uses the author's local credentials (`ANTHROPIC_API_KEY` env). Drives the Haiku KC-extraction step. |
| Docker + nvidia-container-toolkit | latest | Containerized GPU runtime | Mandatory constraint (nitro/Fedora). Base off `pytorch/pytorch:*-cuda12.8-cudnn9-runtime` (or `-devel`). |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pydantic | 2.x | Request/response + config models | Validate uploaded ProgSnap2 metadata, KC edits, training config. Ships with FastAPI. |
| python-multipart | latest | Multipart upload parsing | Required by FastAPI for the dataset-upload form. |
| pandas | 2.x | ProgSnap2 ingestion / EDA | Already used by `data_loader.py`/`code_features.py`. Reads CSVs, builds sequences, powers EDA aggregations. |
| pyarrow | latest | Parquet I/O | Persist normalized per-class datasets as Parquet (fast, typed, compact) instead of re-parsing raw CSV each run. |
| numpy | <2.0 or 2.x — match TCC 1 | Numerics | Transitive PyTorch/pandas dep; pin to TCC 1's line to avoid ABI surprises. |
| javalang | 0.13.0 | Java AST parsing | Mandatory — core of `code_features.py` path extraction. Pure Python, no external CLI. |
| anytree | 2.x | AST tree walking | Used by `code_features.py` (`Node`, `Walker`, `findall_by_attr`). |
| sentence-transformers | 3.x/4.x | Sentence-BERT embeddings | KCGen-KT embedding step. Pulls a transformer model; can run on the same GPU. |
| scikit-learn | 1.4+ | HAC clustering + metrics | `AgglomerativeClustering` for KCGen-KT hierarchical clustering; AUC utilities already in `evaluation.py`. |
| pyBKT | latest | BKT baseline (optional) | Constraint mentions pyBKT reuse; the app core uses only Code-DKT, so this is optional/demo-only. |
| Plotly | 5.x | EDA charts (optional, Python-side) | Use **only if** you want server-generated rich EDA figures (learning curves, heatmaps) embedded as HTML. For the dashboard proper, stay on Chart.js (below). |
| httpx | (via anthropic) | HTTP client | Transitive anthropic dep; no direct use needed. |

### Frontend Assets (no build step)

| Asset | Version | Purpose | Notes |
|-------|---------|---------|-------|
| Tailwind CSS | via `cdn.tailwindcss.com` (Play CDN) | Styling | The prototype already uses the Play CDN. Fine for a single-instance internal tool. If you want to drop the CDN dependency, switch to the Tailwind standalone CLI to emit one static `app.css` — no Node project required. |
| Chart.js | 4.4.x (prototype uses 4.4.0) | Dashboard charts | Already wired into all 6 prototype pages. Keep it. Mastery bars, per-student × KC, accuracy rates — all standard Chart.js. Serve `chart.umd.min.js` locally instead of jsDelivr for offline/Tailscale reliability. |
| HTMX | 2.0.x | AJAX/polling | Single `<script>` tag, served locally. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv (or pip + venv) | Dependency management | `uv` is the 2026 default for fast, reproducible Python installs; a `requirements.txt`/`pyproject.toml` pinned against TCC 1 is the priority. |
| Docker Compose | Orchestrate web + worker + redis | Three services: `web` (uvicorn), `worker` (RQ, gets the GPU), `redis`. Compose makes the single-host nitro deploy reproducible. |
| ruff | Lint/format | Fast, single tool; optional but standard in 2026. |

## Job Execution: How to run live Code-DKT training

| Option | Verdict | Why |
|--------|---------|-----|
| **RQ + Redis** | ✅ Recommended | Simplest *durable, out-of-process* queue. One `rq worker` process = natural GPU serializer. Survives web restarts, exposes job status to poll from HTMX, retries on failure. ~1 small dependency + Redis container. Right complexity for the scope. |
| FastAPI `BackgroundTasks` | ❌ Not for training | Runs in the web process — a multi-minute GPU job blocks/risks the worker, dies on redeploy, and gives no durable status/restart. Fine only for tiny post-response side-effects (e.g. writing a log). |
| Raw `threading`/`asyncio.to_thread` | ❌ Avoid | No durability, no cross-request status store, GIL + CUDA-in-threads is fragile, lost on restart. Tempting but a trap for "training between upload and dashboard." |
| Celery + Redis | ⚠️ Overkill | Powerful but heavy config (beat, routing, serialization gotchas) for a single-user, single-queue tool. Reserve for multi-worker production. |
| Dramatiq | ⚠️ Fine alternative | Cleaner than Celery; legitimate choice. RQ wins on smaller mental model and better casual job-status introspection for a TCC. |

## Frontend Approach: server templates + HTMX (NOT a SPA)

## Charting: Chart.js (keep), Plotly optional

- **Chart.js 4.4.x** for the dashboard — already in the prototype, covers mastery bars, per-student × KC matrices (as stacked/grouped bars or a heatmap plugin), accuracy rates, learning curves. Confidence: HIGH.
- **Plotly (Python)** only if you want richer server-generated EDA figures (annotated heatmaps, interactive learning curves) embedded as standalone HTML. Optional; don't introduce a second JS charting lib (Recharts/ECharts) — that would imply a SPA.
- **Recharts:** only relevant if you go React, which you should not.

## Persistence: SQLite + filesystem (NOT Postgres)

| Data | Store | Format | Rationale |
|------|-------|--------|-----------|
| Classes, assignments, KC definitions, Q-matrix, training-run metadata, job status | **SQLite** | one `app.db` file | Single writer, embedded, zero ops, trivially backed up/version-pinned. Relational shape (class → assignment → KC → Q-matrix entries) fits SQL cleanly. |
| Uploaded raw ProgSnap2 datasets | **Filesystem** | original CSVs under `data/<class>/raw/` | Keep originals for reproducibility/re-ingest. |
| Normalized per-class sequences / features | **Filesystem** | **Parquet** (pyarrow) | Fast typed reload between training runs; avoids re-parsing CSV + re-extracting AST paths every time. |
| Trained Code-DKT model artifacts | **Filesystem** | `torch.save` → `.pt` per (class, assignment) + a small `vocab.pkl` (token/path maps) | Models are binary blobs; the FS is the right place. SQLite stores the *path* + metadata, not the blob. Persist `state_dict` + the exact config/vocab so re-load is deterministic. |
| KCGen-KT embeddings cache | **Filesystem** | `.npy`/Parquet | Cache Sentence-BERT outputs to avoid recompute on re-cluster. |

## Containerization: PyTorch CUDA image on Fedora/nitro

- **Base image:** `pytorch/pytorch:2.7.x-cuda12.8-cudnn9-runtime` (use `-devel` only if you must compile extensions; `runtime` is smaller). Pin the tag matching the TCC 1 PyTorch line. Alternative: `nvidia/cuda:12.8.x-cudnn-runtime-ubuntu22.04` + `pip install torch` if you want tighter control.
- **GPU access:** install **`nvidia-container-toolkit`** on the Fedora host, configure the Docker runtime (`nvidia-ctk runtime configure`), and grant the **worker** container `--gpus all` (or `deploy.resources.reservations.devices` in Compose). Only the RQ worker needs the GPU; web + redis do not.
- **Fedora note:** Fedora often runs SELinux + a recent kernel; the `nvidia-container-toolkit` cdi/runtime path is the reliable approach in 2026. Verify with `docker run --rm --gpus all <img> nvidia-smi`. Defer host-specific firewall/Tailscale/SELinux specifics to the `nitro-env` skill at deploy time.
- **Compose topology:**

## Anthropic SDK usage (KCGen-KT)

- Credentials come from the author's **local** environment (`ANTHROPIC_API_KEY`); no hosted/prod key, consistent with "no public deploy."
- Run KC extraction as its own RQ job (it's network-bound and slow over many samples) — same queue, separate from GPU training; the dashboard polls its status the same way.
- Add simple **retry + caching**: persist each prompt→KC response (keyed by code-sample hash) to the FS so re-runs and teacher re-validation don't re-bill/re-call. Use the SDK's built-in retry plus an idempotency cache.
- Keep the pipeline deterministic-ish: low temperature, fixed prompt templates, store the model id + prompt version alongside results for reproducibility in the TCC.

## Installation

# Backend core

# ML / reuse (pin torch to the TCC 1 line; cu128 wheels)

# LLM

# Optional server-side EDA charts

# Frontend assets (no build step): vendor these as static files

#   htmx 2.0.x        -> /static/js/htmx.min.js

#   chart.js 4.4.x    -> /static/js/chart.umd.min.js

#   tailwind          -> Play CDN, or standalone CLI -> /static/css/app.css

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| FastAPI | Django | If you needed an admin panel, ORM-heavy multi-model CRUD, and auth out of the box. Single-instance no-login tool doesn't justify its weight. |
| FastAPI | Streamlit | Tempting for a "quick ML dashboard," but it fights you on long background jobs, custom multi-page UX, the existing Tailwind/Chart.js prototype, and serving HTML fragments. Reproducing the 6-page prototype in Streamlit is harder, not easier. |
| FastAPI | Flask | Viable (Flask + Jinja + HTMX + RQ is a classic combo). FastAPI wins on async, Pydantic validation, and native job-status JSON endpoints. Flask is a fine fallback if the team prefers WSGI simplicity. |
| RQ | Celery | Multi-worker, multi-queue, scheduled production workloads. |
| RQ | Dramatiq | Equally valid; pick it if you prefer its API. RQ chosen for smaller mental model + easy job introspection. |
| Jinja+HTMX | React + Recharts (SPA) | Only if the dashboard needs heavy client-side cross-filtering/interactivity beyond requirements. |
| SQLite | Postgres | Multi-user, networked, concurrent writers, or >single-instance — none apply here. |
| Chart.js | Plotly.js / ECharts | If you adopt a SPA or need 3D/very large interactive plots. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| FastAPI `BackgroundTasks` for training | Runs in-process; a multi-minute GPU job blocks/risks the web worker and dies on restart with no durable status | RQ job in a dedicated worker |
| Raw threads/`asyncio` for training | No durability, no status store, CUDA-in-threads fragility, lost on restart | RQ job |
| Multiple uvicorn web workers | Forked workers duplicate state and race the single GPU/SQLite writer | `--workers 1` web + one RQ worker |
| Postgres / a separate DB server | Operational weight with zero benefit for single-instance | SQLite |
| Pickling everything (datasets + models in one blob) | Version-brittle, unqueryable | SQLite for state, `.pt`/Parquet for blobs |
| A React/Vue SPA + bundler | Adds a second language, build pipeline, and API/CORS plumbing for UX you already have via Tailwind+HTMX | Jinja2 + HTMX |
| HTMX 4.0 beta | Still beta/`fetch`-rewrite in mid-2026; API churn risk for a thesis deadline | HTMX 2.0.x stable |
| `latest` Docker tags / unpinned torch | Breaks scientific reproducibility (numerics, seeds) | Pin torch + CUDA + image tag to the TCC 1 environment |
| Letting the web container hold the GPU | Wastes VRAM, encourages in-process training | GPU on the RQ worker only |

## Stack Patterns by Variant

- Use PyTorch ≥ 2.7 cu128 (first line with sm_120 wheels).
- Any PyTorch 2.x cu12x line works; still pin to the TCC 1 version for reproducibility.
- Vendor Tailwind via the standalone CLI (emit `app.css`), and serve htmx + chart.js from `/static`. No Node project required.
- Run KCGen-KT as its own RQ job (separate from GPU training), cache prompt→KC responses on the FS keyed by code-sample hash.

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| PyTorch 2.7.x (cu128) | CUDA 12.8 runtime, cuDNN 9 | Match the host driver; `pytorch/pytorch:*-cuda12.8-cudnn9-*` image bundles them. |
| FastAPI 0.137.x | Python ≥ 3.10, Pydantic 2.x, Starlette current | `fastapi[standard]` pulls uvicorn + jinja2 + multipart. |
| RQ 2.x | Redis ≥ 5 / Valkey ≥ 7.2, Python ≥ 3.9 | Redis 7.2 recommended. |
| anthropic 0.107.x | Python ≥ 3.8, httpx/pydantic | Pulls its own httpx; no version pin needed by you. |
| javalang 0.13.0 | Python 3.x | Pure Python; same version as TCC 1 for identical AST output (reproducibility). |
| numpy | torch + pandas line of TCC 1 | Pin to TCC 1 to avoid ABI/2.0 breakage; verify against the trained-model numerics. |
| Chart.js 4.4.x | Modern browsers | Already validated in the prototype. |
| HTMX 2.0.x | Any backend | Pin minor; avoid 4.0 beta. |

## Sources

- https://pypi.org/project/fastapi/ — FastAPI latest (0.137.0, 2026-06-14), Python ≥ 3.10 — HIGH
- https://pypi.org/project/anthropic/ — anthropic SDK latest (0.107.x) — HIGH
- https://github.com/bigskysoftware/htmx/releases + npm htmx.org — HTMX 2.0.x stable, 4.0 in beta (2026) — HIGH
- https://pytorch.org/blog/pytorch-2-7/ — PyTorch 2.7 cu128 / Blackwell support — HIGH
- https://github.com/rq/rq + python-rq.org — RQ 2.x, Redis ≥ 5/Valkey 7.2, Python ≥ 3.9 — HIGH
- https://hub.docker.com/r/pytorch/pytorch + https://hub.docker.com/r/nvidia/cuda — CUDA 12.x devel/runtime base images — HIGH
- Prototype `docs/tcc2_prototipo.html` — confirms Tailwind Play CDN + `chart.js@4.4.0` already in use — HIGH (direct inspection)
- `src/models/code_dkt.py`, `src/code_features.py` — confirms PyTorch/javalang/anytree/pandas/numpy reuse + CUDA device selection — HIGH (direct inspection)
- `.planning/PROJECT.md` — single-instance, Docker+GPU on nitro, local Claude account, scientific reproducibility constraints — HIGH

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| modular-design-principles | > Technology-agnostic guidance for modular systems: bounded contexts, clear boundaries, composability, state isolation, explicit contracts, failure containment, scaffolding workflows, split/merge criteria, sub-units inside a context, and compliance review signals. Use when designing or reviewing module structure, service boundaries, package layout, cross-cutting dependencies, "how should we split this?", modularity assessments, coupling between domains, greenfield context design, or architecture discussions without assuming a specific framework, language, or repository layout. Do NOT use for executing the full Patterns 1–5 repo decomposition pipeline or per-pattern inventories (use modular-decomposition), phased extraction roadmaps as the main deliverable (use decomposition-planning-roadmap), or end-to-end legacy migration strategy (use legacy-migration-planner). | `.claude/skills/modular-design-principles/SKILL.md` |
| react-composition-patterns | React composition patterns that scale. Use when refactoring components with boolean prop proliferation, building flexible component libraries, or designing reusable APIs. Triggers on tasks involving compound components, render props, context providers, or component architecture. Includes React 19 API changes. Do NOT use for React/Next.js performance optimization (use react-best-practices instead). | `.claude/skills/react-composition-patterns/SKILL.md` |
| tdd | Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development. | `.claude/skills/tdd/SKILL.md` |
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
