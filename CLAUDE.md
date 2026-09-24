## Project

**EDM·KT, Ferramenta Docente (TCC 2)**

Aplicação web docente que aplica *knowledge tracing* a dados de programação introdutória
(formato ProgSnap2) para mostrar ao professor, **durante a disciplina**, o estágio de domínio da
turma por *Knowledge Component* (KC). O professor sobe os dados da própria turma, o app extrai e
valida KCs, treina um modelo **Code-DKT** sobre aquele dado e apresenta um dashboard de *mastery*
por aluno × KC, com os KCs críticos, os alunos em atenção e recomendações de reforço.

É a **fase de Implantação** do processo EDM iniciado no TCC 1 (pesquisa em `../tcc.edm.kt`), que
comparou BKT, DKT e Code-DKT e elegeu o Code-DKT como modelo base.

O que precisa funcionar acima de tudo é o professor enxergar **quais conceitos a turma ainda não
domina**, em dados reais da própria turma, a tempo de ajustar as aulas. Ou seja, dados → KCs →
Code-DKT treinado → dashboard de mastery.

### Constraints

- **Runtime.** Servidor **nitro** (Fedora) via **Docker**, com **GPU** para o treino, acesso pelo
  browser via Tailscale. Docker, portas, firewall e GPU seguem o skill `nitro-env`.
- **Reprodutibilidade científica** (Code-DKT fiel a Shi et al. 2022, não alterar). R=50 paths,
  max_path_length=8, max_path_width=2, embeddings 100-dim → 300-dim, LSTM hidden_dim=128,
  dropout=0.1, Adam lr=5e-4, 40 épocas, batch=128, grad clip=10, seed=42. Métrica primária é o
  first-attempt AUC.
- **Entrada.** ProgSnap2 v6 (CodeStateID → snapshot de código Java, Score ∈ [0,1]). O rótulo é
  Score == 1.0. KCs iniciais via KCGen-KT, validados pelo professor.
- **Performance.** O treino é por assignment e leva minutos na GPU, então a UX tem uma etapa de
  treino entre o upload e o dashboard.
- **Sem prazo rígido.** Qualidade e fidelidade científica vêm antes de velocidade.

## Stack

### Backend

| Peça | Versão | Papel |
|---|---|---|
| Python | 3.11 (conda da imagem base) | Linguagem do backend |
| FastAPI + Uvicorn | | API **JSON pura**, `--workers 1` (escritor único e GPU compartilhada) |
| PyTorch | 2.7.1+cu128 | Treino e inferência do Code-DKT, na GPU do mesmo container da API |
| SQLite (`sqlite3` stdlib) | | `app.db` com turmas, assignments, o dado limpo, problemas, KCs, jobs e modelos. Sem ORM |
| pandas | | Ingestão ProgSnap2 e o dado limpo em DataFrame |
| javalang + anytree | 0.13.0 / 2.x | Paths da AST Java (a feature do Code-DKT) |
| sentence-transformers | 5.4.1 | Embeddings SBERT do KCGen-KT |
| scikit-learn | | Clustering de KCs (HAC + silhouette) e AUC |
| CLI `claude` | Haiku 4.5 pinado | Geração de KCs pela **assinatura** (OAuth montado read-only). O SDK `anthropic` nunca é importado |

### Web (`src/web/`)

| Peça | Versão | Papel |
|---|---|---|
| React | 19.2 | SPA servida pelo dev server do Vite |
| Vite | 8.x | Build e dev server, com proxy same-origin para a API (sem CORS) |
| TypeScript | 6.x | |
| TanStack Query | 5.101 | Estado de servidor, cache por `queryKey`, `retry` desligado |
| Chart.js + react-chartjs-2 | 4.5 / 5.3 | Gráficos das estatísticas pré-treino |
| Vitest + Testing Library | | Os testes rodam **no container**, nunca com npm no host |

### Jobs

Treino e geração de KCs rodam em **subprocess**
(`python -m api.<funcionalidade>.presentation.workers.<…>_worker`), um por vez, serializados pelo
`OneJobAtATimeLock` (uma linha no banco, validada pela vida do PID do dono, sem TTL). O banco é o
canal entre os processos, e o estado do job vive em `training_job` e `kc_job`. Um restart no meio
do treino perde o job, e isso é aceito.

### Runtime

Dois serviços em `docker-compose.yml`. A `api` não publica porta e só é alcançável pelo nome do
serviço. O `web` publica em `${EDMKT_BIND_IP:-127.0.0.1}:5173`. GPU RTX 4050, 6 GB de VRAM.

### O que NÃO usar

| Evitar | Por quê |
|---|---|
| Vários workers do uvicorn | Forks duplicam estado e disputam a GPU e o escritor único do SQLite |
| Redis, RQ, Celery | Instância única, a trava já serializa |
| Postgres ou outro servidor de banco | Sem multiusuário nem concorrência de escrita, só peso operacional |
| `BackgroundTasks` ou threads para treino | Bloqueia o processo web, morre no restart, sem status durável |
| Instalar dependências no host (npm, pip) | Regra dura, as dependências vivem **só no container** |
| Tag `latest` ou torch sem pin | Quebra a reprodutibilidade (o teste de regressão é o oráculo) |
| Uma segunda biblioteca de gráficos | Chart.js cobre o dashboard |
| Porta publicada sem bind IP explícito | O Docker escreve nftables próprio e passa por cima do firewalld, vazando na LAN |

## Conventions

Nomes em inglês, PEP 8, dizendo a intenção (`StartTrainingUseCase`, `find_students_at_risk()`).
Todo nome sai de `docs/GLOSSARY.md`, e um conceito novo entra no glossário antes de entrar no
código. Testes ficam ao lado do arquivo testado, com sufixo `_test.py`. Comentários só com `#`, de
uma linha, sem travessão nem dois-pontos (verificado por `src/api/code_comments_test.py`), e o
porquê completo das decisões não óbvias fica em `docs/DECISIONS.md`.

## Architecture

`src/ml/` é a ciência e nunca importa de `api/`. `src/web/` é a SPA. `src/api/` é organizada por
funcionalidade (`classrooms`, `assignments`, `classroom_import`, `knowledge_components`,
`model_training`, `mastery_dashboard`, `shared`), cada uma com `domain/ application/
infrastructure/ presentation/` e, dentro delas, uma subpasta por papel. Uma funcionalidade pode
ter uma sub-funcionalidade com camadas próprias (`assignments/problems/`). As regras estão em
`docs/ARCHITECTURE.md` e são verificadas pelo `import-linter` e por `src/api/architecture_test.py`.
