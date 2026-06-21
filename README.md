# EDM·KT — Ferramenta Docente (TCC 2)

Aplicação web docente que aplica *knowledge tracing* (Code-DKT) a dados de programação
introdutória em formato ProgSnap2, mostrando ao professor o estágio de domínio da turma
por *Knowledge Component* (KC). Esta é a fase de **Implantação** do processo EDM iniciado
no TCC 1 (`../tcc.edm.kt`), que elegeu o Code-DKT como modelo base.

O núcleo científico vive em `src/edmkt_core/` — um port fiel do pipeline Code-DKT do TCC 1
(commit `0e8807c`), test-driven e blindado por testes de caracterização. O contrato público
é `train_and_evaluate` (DataFrame ProgSnap2 entra, artefatos saem).

## Reprodutibilidade científica

A fidelidade numérica do TCC 1 é travada como um **teste de regressão golden-run**
(`tests/test_golden_run.py`): retreina o Code-DKT no CSEDM real (Spring 2019, AssignmentID
439) e exige que a **first-attempt AUC** caia na banda de ±3pp **[0.7027, 0.7627]**, ancorada
no valor de referência do TCC 1 **73.2654%** (`../tcc.edm.kt/results/comparison_summary.json`,
Code-DKT A439). Fora da banda o teste **falha alto** — qualquer mudança de dependência, seed
ou ordem de operações que mova o A439 para fora da banda fica vermelha.

A banda de ±3pp absorve a variação de seed (std ≈ 1.34pp no TCC 1) e a diferença entre o
`FROZEN_CONFIG` (protocolo Shi et al. 2022: `hidden_dim=128`, `dropout=0.1`) e o
`BEST_CONFIG` do grid do TCC 1 (`hidden_dim=200`). O valor observado neste repositório com o
`FROZEN_CONFIG` é **0.7608**, dentro da banda.

### Pré-requisito: `EDMKT_CSEDM_PATH`

O golden-run lê o dataset CSEDM real a partir da variável de ambiente `EDMKT_CSEDM_PATH`,
que aponta para o dataset provisionado em `datasets/CSEDM/` (gitignored — nunca versionado, D-12):

```
$EDMKT_CSEDM_PATH/
├── MainTable.csv               # eventos ProgSnap2 (Run.Program / Compile.Error, Score)
├── CodeStates/CodeStates.csv   # CodeStateID -> snapshot de código Java
└── LinkTables/Subject.csv      # SubjectID -> X-Grade
```

Quando `EDMKT_CSEDM_PATH` não está setada, o golden-run **pula com motivo claro** — o suite
rápido continua verde em máquinas sem o dataset (gate *fast-by-default*).

## Rodando os testes (somente via Docker — host limpo)

Todas as dependências de ML vivem **apenas** dentro da imagem `edmkt-core:dev` (nunca no host
nitro, nunca em venv de host). `--security-opt label=disable` é obrigatório em todo `docker run`
para ler os bind mounts de `/srv` sem relabel SELinux.

### Suite rápido (padrão — golden-run desmarcado, CPU)

```bash
docker run --rm --security-opt label=disable -v "$PWD":/app -w /app \
  edmkt-core:dev python -m pytest tests/ -q
```

O `addopts = -m 'not golden'` (em `pyproject.toml`) desmarca o golden-run por padrão.

### Suite completo com golden-run (GPU + dataset)

```bash
docker run --rm --gpus all --security-opt label=disable \
  -v "$PWD":/app -w /app \
  -v "$PWD/datasets/CSEDM":/data/CSEDM:ro \
  -e EDMKT_CSEDM_PATH=/data/CSEDM \
  edmkt-core:dev python -m pytest tests/test_golden_run.py -m golden -q -s
```

O treino são 40 épocas sobre o A439 — leva alguns minutos na GPU (RTX 4050; a dGPU acorda sob
demanda). `torch.cuda.is_available()` deve ser `True` na imagem; caso contrário o run cai para
CPU (mais lento, ainda dentro da banda por D-10).

### Checagem pesada sob demanda (não roda por padrão — D-07)

A verificação mais robusta (multi-seed 42–51 × os 5 assignments) é executada **manualmente**
antes de marcos, não no gate de cada commit. O golden-run aqui é o portão de treino único
*fast-by-default*; a banda de ±3pp é o critério de aceite.

## Dependências travadas

`requirements.lock` fixa as versões exatas validadas pelo golden-run (o oráculo de versões,
RESEARCH A2). A âncora real de reprodutibilidade é a **tag fixa da imagem Docker**
(`pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime`, em `Dockerfile`), cujo ambiente conda fornece
`torch==2.7.1+cu128` e `numpy==2.2.6` — não instaláveis como pin simples de PyPI. Construa a
partir dessa tag para reproduzir as numéricas.
