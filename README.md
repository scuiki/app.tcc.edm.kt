# EDM·KT — Ferramenta Docente (TCC 2)

Aplicação web docente que aplica *knowledge tracing* (Code-DKT) a dados de programação
introdutória em formato ProgSnap2, mostrando ao professor o estágio de domínio da turma
por *Knowledge Component* (KC). Esta é a fase de **Implantação** do processo EDM iniciado
no TCC 1 (`../tcc.edm.kt`), que elegeu o Code-DKT como modelo base.

O código vive em `src/`, em três partes:

- `src/ml/` — a ciência: o Code-DKT, que segue Shi et al. (2022) pelas decisões de
  [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md), e o KCGen-KT, portado do TCC 1 (commit `0e8807c`),
  os dois blindados por testes de caracterização. Não conhece a aplicação.
- `src/api/` — a aplicação FastAPI, organizada por funcionalidade, cada uma com as camadas
  `domain/`, `application/`, `infrastructure/` e `presentation/`.
- `src/web/` — a SPA em React (Vite + TypeScript) que o professor usa no navegador.

Os nomes estão em [`docs/GLOSSARY.md`](docs/GLOSSARY.md) e as camadas e a regra de dependência
em [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). Cada teste fica ao lado do arquivo que testa
(`<arquivo>_test.py`); `tests/` guarda só o teste de regressão, a comparação com o paper, as
fixtures e os dados de exemplo.

## Reprodutibilidade científica

O Code-DKT segue Shi et al. (2022) pelas decisões registradas em
[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md). O resultado numérico é travado por um **teste de
regressão** (`tests/test_regression_a439.py`) que retreina o Code-DKT no CSEDM real (Spring 2019,
AssignmentID 439) com as dez seeds de 42 a 51 e exige que a **média do first-attempt AUC** fique
dentro da **tolerância** de **±0,001** (±0,1 ponto) em torno da **média de referência 0,7278**, ou
seja, em **[0,7268, 0,7288]**. Fora da tolerância o teste **falha alto**, e qualquer mudança de
código, dependência, seed ou ordem de operações que mova a média fica vermelha.

O teste detecta mudança de comportamento do código. Ele **não serve** de valor de referência
científico, nem contra o TCC 1 nem contra o paper. O 0,7278 é a média que o app mediu no A439 em
02/10/2026, e a tolerância é estreita porque as dez seeds se repetem bit a bit em processos
diferentes, o que deixa só o ruído de float do ambiente. Uma troca de driver, de GPU ou de
dependência que tire a média da tolerância pede uma nova medição da média de referência, registrada
em `docs/DEVELOPMENT.md`.

Com as dez seeds, o A439 deu **72,78 ± 0,81** na primeira tentativa e **69,25 ± 0,86** no geral
(média e desvio amostral, em porcentagem), e a seed 42 sozinha dá 0,7228. A comparação com o paper
está mais abaixo.

A repetição bit a bit depende do `PYTHONHASHSEED=0`, que a imagem fixa, da partição por exercício
do repositório oficial (386 alunos no A439, 78 no teste), da amostragem aleatória de R=100 paths
com a `path_sampling_seed` 42 e do cuDNN determinístico. O fixture do CSEDM falha, em vez de pular,
quando o `PYTHONHASHSEED` não é 0.

### Pré-requisito: `EDMKT_CSEDM_PATH`

O teste de regressão lê o dataset CSEDM real a partir da variável de ambiente `EDMKT_CSEDM_PATH`,
que aponta para o dataset provisionado em `datasets/CSEDM/` (ignorado pelo git, grande demais para
ser versionado):

```
$EDMKT_CSEDM_PATH/
├── MainTable.csv               # eventos ProgSnap2 (Run.Program / Compile.Error, Score)
├── CodeStates/CodeStates.csv   # CodeStateID -> snapshot de código Java
└── LinkTables/Subject.csv      # SubjectID -> X-Grade
```

Quando `EDMKT_CSEDM_PATH` não está setada, o teste de regressão **pula com motivo claro** — a suíte
rápida continua verde em máquinas sem o dataset (a suíte padrão não depende dele).

## Rodando os testes (somente via Docker — host limpo)

Todas as dependências de ML vivem **apenas** dentro da imagem `edmkt-core:dev` (nunca no host
nitro, nunca em venv de host). `--security-opt label=disable` é obrigatório em todo `docker run`
para ler os bind mounts de `/srv` sem relabel SELinux.

### Suite rápido (padrão — teste de regressão desmarcado, CPU)

```bash
docker run --rm --security-opt label=disable -v "$PWD":/app -w /app \
  edmkt-core:dev python -m pytest -q
```

A regra de dependência entre camadas é verificada pelo `import-linter` (também no container):

```bash
docker run --rm --security-opt label=disable -v "$PWD":/app -w /app edmkt-core:dev \
  sh -c "pip install -q import-linter==2.15 && PYTHONPATH=/app/src lint-imports"
```

O `addopts = -m 'not regression and not literature'` (em `pyproject.toml`) desmarca o teste de
regressão e a comparação com o paper por padrão.

### Suite completo com o teste de regressão (GPU + dataset)

```bash
docker run --rm --gpus all --security-opt label=disable \
  -v "$PWD":/app -w /app \
  -v "$PWD/datasets/CSEDM":/data/CSEDM:ro \
  -e EDMKT_CSEDM_PATH=/data/CSEDM \
  edmkt-core:dev python -m pytest tests/test_regression_a439.py -m regression -q -s
```

São dez treinos de 40 épocas no A439, um por seed, e levam cerca de 4 minutos na RTX 4050. A média
de referência foi medida na GPU, então `torch.cuda.is_available()` tem de ser `True` na imagem, e
sem GPU o teste falha. O comando roda também a conferência da partição do A439 contra o
procedimento do repositório oficial (386 alunos, 78 no teste), que não treina. O `-s` mostra a
média e o AUC de cada seed.

### Comparação com o paper (sob demanda, com a api parada)

```bash
docker run --rm --gpus all --security-opt label=disable \
  --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD":/app -w /app \
  -v "$PWD/datasets/CSEDM":/data/CSEDM:ro \
  -e EDMKT_CSEDM_PATH=/data/CSEDM \
  edmkt-core:dev python -m pytest tests/test_literature_comparison.py -m literature -q -s
```

Treina os cinco exercícios da CSEDM com as dez seeds de 42 a 51, em cerca de 19 minutos na
RTX 4050, e imprime a média e o desvio ao lado das Tabelas 1 e 2 de Shi et al. (2022), sem asserção
contra elas. A tabela medida e a leitura dela estão em `docs/DEVELOPMENT.md`. O AUC de cada seed fica em
`docs/results/code_dkt_literature_comparison.json`, que é versionado, e o `--user` faz o arquivo
sair com o seu usuário, e não com o root do container. Rodar um exercício só (`-k 439`) atualiza
só a parte dele no arquivo.

## Dependências travadas

`requirements.lock` fixa as versões exatas do ambiente em que o teste de regressão mediu o 0,7278,
e uma troca de versão que mude o resultado numérico tira a média da tolerância de ±0,1 ponto (teste
vermelho). A âncora real de reprodutibilidade é a **tag fixa da imagem Docker**
(`pytorch/pytorch:2.7.1-cuda12.8-cudnn9-runtime`, em `Dockerfile`), cujo ambiente conda fornece
`torch==2.7.1+cu128` e `numpy==2.2.6`, que não se instalam como pin simples de PyPI. O `Dockerfile`
também fixa `PYTHONHASHSEED=0`, porque a ordem dos modificadores Java nos AST paths sai de um set e
depende dessa semente. A imagem do app (`deploy/Dockerfile.app`) deriva dela e herda a variável.
Construa a partir dessa tag para reproduzir os resultados numéricos.

As versões das bibliotecas que definem o resultado numérico na imagem atual são torch 2.7.1+cu128,
numpy 2.2.6, pandas 2.3.3, javalang 0.13.0, anytree 2.13.0, scikit-learn 1.9.0 e scipy 1.17.1. As
demais estão no `requirements.lock`.
