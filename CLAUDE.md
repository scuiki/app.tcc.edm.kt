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
  (PyTorch, pyBKT) embrulhado na biblioteca `ml`. Frontend **React SPA (Vite + TS)**,
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

## Stack (o que está construído)

> Esta seção descreve o sistema **como ele é**. O relatório de pesquisa de stack que a
> precedeu — anterior às decisões tomadas, e divergente delas — segue em
> `.planning/research/STACK.md` como histórico.

### Backend — Python

| Peça | Versão | Papel |
|---|---|---|
| Python | 3.11 (conda da imagem base) | Linguagem do backend |
| FastAPI + Uvicorn | — | API **JSON pura**; `--workers 1` (escritor único + GPU compartilhada) |
| PyTorch | 2.7.1+cu128 | Treino/inferência do Code-DKT, na GPU do mesmo container da API |
| SQLite (`sqlite3` stdlib) | — | `app.db`: turmas, assignments, KCs, Q-matrix, jobs, artefatos. Sem ORM |
| pandas + pyarrow | pyarrow 24.0.0 | Ingestão ProgSnap2 e Parquet canônico por assignment |
| javalang + anytree | 0.13.0 / 2.x | Extração de paths de AST Java (features do Code-DKT) |
| sentence-transformers | 5.4.1 | Embeddings SBERT do pipeline KCGen-KT |
| scikit-learn | — | HAC + silhouette (clustering de KCs) e AUC |
| CLI `claude` | Haiku 4.5 pinado | Geração de KCs pela **assinatura** (OAuth montado read-only). O SDK `anthropic` NUNCA é importado |

Pacotes em `src/`: `ml/` é a ciência pura (Code-DKT, KCGen-KT, mastery) e nunca importa de
`api`; `api/` é a aplicação, organizada por funcionalidade (`assignments`, `classroom_import`,
`knowledge_components`, `model_training`, `mastery_dashboard`, mais `shared/`), cada uma com
`domain/`, `application/`, `infrastructure/` e `presentation/`. Nomes em `docs/GLOSSARY.md`;
regra de dependência (verificada pelo `lint-imports`) em `docs/ARCHITECTURE.md`.

### Frontend — React SPA

| Peça | Versão | Papel |
|---|---|---|
| React | 19.2 | SPA servida pelo dev server do Vite |
| Vite | 8.x | Build e dev server; proxy same-origin para `http://api:8099` (sem CORS) |
| TypeScript | 6.x | — |
| TanStack Query | 5.101 | Estado de servidor: cache por `queryKey`, loading/erro, `retry: false` |
| Chart.js + react-chartjs-2 | 4.5 / 5.3 | Gráficos da EDA |
| Vitest + Testing Library | — | Gates rodam **no container**, nunca com npm no host |
| openapi-typescript | 7.13 | Gera `src/api/schema.d.ts` a partir do OpenAPI do FastAPI |

### Execução de jobs

Treino e geração de KCs rodam em **subprocess** (`python -m api.model_training.presentation.training_worker`), serializados por
uma **trava global**: uma linha em `pipeline_lock` com `holder_pid`, validada por liveness de PID,
sem TTL. O banco é o canal entre os processos — o retorno do fire-and-forget se perde, o estado
vive em `training_job` / `kc_job`.

**Sem Redis, sem RQ, sem Celery.** Instância única, um pipeline por vez: a trava basta. Tradeoff
aceito — um restart no meio do treino perde o job (re-treina).

### Runtime

Docker no nitro (Fedora), dois serviços em `docker-compose.yml`: `api` (não publica porta alguma;
alcançável só pelo nome de serviço na rede do compose) e `frontend` (publica em
`${EDMKT_BIND_IP:-127.0.0.1}:5173`). GPU RTX 4050, 6 GB de VRAM. Bind de portas, firewall e GPU
seguem o skill `nitro-env`.

### O que NÃO usar

| Evitar | Por quê |
|---|---|
| Múltiplos workers do uvicorn | Forks duplicam estado e disputam a GPU e o escritor único do SQLite |
| Redis / RQ / Celery | Escopo de instância única; a trava global já serializa |
| Postgres ou outro servidor de banco | Sem multiusuário e sem concorrência de escrita: peso operacional sem ganho |
| `BackgroundTasks` ou threads para treino | Bloqueia o processo web, morre no restart, sem status durável |
| Instalar deps no host (npm/pip) | Regra dura: dependências vivem **só no container** |
| Tag `latest` ou torch não pinado | Quebra a reprodutibilidade científica (o teste de regressão é o oráculo) |
| Um segundo lib de gráficos | Chart.js já cobre tudo que o dashboard precisa |
| Porta publicada sem bind IP explícito | Docker escreve nftables próprio e passa por cima do firewalld: vaza na LAN |

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Nomes em inglês, PEP 8, dizendo a intenção (`StartTrainingUseCase`, `find_students_at_risk()`).
Todo nome sai de `docs/GLOSSARY.md`; conceito novo entra no glossário antes de entrar no código.
Testes ficam ao lado do arquivo testado, com sufixo `_test.py`. Detalhes em `docs/ARCHITECTURE.md`.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

`src/ml/` é a ciência (nunca importa de `api/`). `src/api/` é organizada por funcionalidade
(`assignments`, `classroom_import`, `knowledge_components`, `model_training`, `mastery_dashboard`,
`shared`), cada uma com `domain/ application/ infrastructure/ presentation/`. A regra de dependência
e a de imports entre funcionalidades estão em `docs/ARCHITECTURE.md` e são verificadas pelo
`import-linter`.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

| Skill | Description | Path |
|-------|-------------|------|
| modular-design-principles | > Technology-agnostic guidance for modular systems: bounded contexts, clear boundaries, composability, state isolation, explicit contracts, failure containment, scaffolding workflows, split/merge criteria, sub-units inside a context, and compliance review signals. Use when designing or reviewing module structure, service boundaries, package layout, cross-cutting dependencies, "how should we split this?", modularity assessments, coupling between domains, greenfield context design, or architecture discussions without assuming a specific framework, language, or repository layout. Do NOT use for executing the full Patterns 1–5 repo decomposition pipeline or per-pattern inventories (use modular-decomposition), phased extraction roadmaps as the main deliverable (use decomposition-planning-roadmap), or end-to-end legacy migration strategy (use legacy-migration-planner). | `.claude/skills/modular-design-principles/SKILL.md` |
| react-composition-patterns | React composition patterns that scale. Use when refactoring components with boolean prop proliferation, building flexible component libraries, or designing reusable APIs. Triggers on tasks involving compound components, render props, context providers, or component architecture. Includes React 19 API changes. Do NOT use for React/Next.js performance optimization (use react-best-practices instead). | `.claude/skills/react-composition-patterns/SKILL.md` |
| tdd | Test-driven development with red-green-refactor loop. Use when user wants to build features or fix bugs using TDD, mentions "red-green-refactor", wants integration tests, or asks for test-first development. | `.claude/skills/tdd/SKILL.md` |
<!-- GSD:skills-end -->

## Planning artifacts

`.planning/` é **histórico**, não estado vivo: registra as decisões e o caminho das Fases 1–6.1
sob o GSD, que foi desinstalado. Vale como referência de *por que* algo é do jeito que é —
mas `STATE.md` e `ROADMAP.md` não descrevem mais o presente e não devem ser atualizados.

Ritmo de trabalho: discutir → planejar → aprovar → executar (ver CLAUDE.md global).
