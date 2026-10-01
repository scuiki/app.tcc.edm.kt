# Arquitetura do backend

Três partes em `src/`. A maior parte deste documento trata das duas em Python (`ml/` e `api/`); a
terceira, `web/`, é a SPA em React, com o próprio `package.json`, e tem a sua seção no fim
([Frontend](#frontend)).

- **`ml/`**: a ciência (Code-DKT, KCGen-KT, AUC). É uma biblioteca, como o
  torch: não conhece HTTP, banco nem disco da aplicação, e **nunca importa de `api/`**. É o que o
  teste de regressão contra o TCC 1 exercita.
- **`api/`**: a aplicação. Organizada **por funcionalidade primeiro**, com as camadas de clean
  architecture dentro de cada uma.

Os nomes seguem o [glossário](GLOSSARY.md).

## Funcionalidades

| Pasta | Responsabilidade |
|---|---|
| `api/classrooms/` | `Classroom`, a turma do professor, o CRUD dela e o `ClassroomStatus` |
| `api/assignments/` | `Assignment` e o ciclo de `AssignmentStatus`. O assignment pertence a uma turma, e todas as outras funcionalidades dependem dele |
| `api/assignments/problems/` | `Problem`, os problemas de cada assignment e a descrição que o LLM deduz. É uma sub-funcionalidade de `assignments`, com camadas próprias |
| `api/classroom_import/` | Upload do ProgSnap2, validação, limpeza, checagem de treinabilidade |
| `api/knowledge_components/` | Gerar KCs com o LLM, editar os KCs de cada problema e aprová-los |
| `api/model_training/` | Disparar e acompanhar o treino do Code-DKT, guardar os modelos |
| `api/mastery_dashboard/` | O que aconteceu nas execuções e o que o modelo prevê, por problema, conceito e aluno |
| `api/shared/` | O que todas usam: erros, base de use case, banco, trava, settings |

Toda funcionalidade tem as quatro pastas, mesmo que alguma fique com um arquivo só. Dentro de
cada camada, os arquivos se separam **por papel**, uma subpasta por papel. Uma subpasta só existe
quando tem conteúdo:

```
<funcionalidade>/
  domain/
    entities/         as entidades: têm identidade (id) e ciclo de vida
    value_objects/    valores sem identidade, imutáveis (ClassroomSlug, MasteryLevel, TrainingOutcome…)
    interfaces/       TODOS os Protocols que outra camada implementa, repositórios inclusive
    rules/            as regras de negócio (IBusinessRule) que os use cases de escrita checam
    services/         lógica de negócio pura, em funções (limpeza, treinabilidade, classificação…)
  application/
    use_cases/        um arquivo por use case
    dtos/             a entrada e a saída dos use cases
    interfaces/       os Protocols que a aplicação precisa (IUnitOfWork, IJobLock…)
    services/         lógica de aplicação usada por mais de um use case
  infrastructure/
    repositories/     as implementações SQLite das interfaces de repositório
    implementations/  as demais implementações (ml/, LLM, disco, leitores) e seus ajudantes
  presentation/
    controllers/      as rotas HTTP (FastAPI)
    workers/          a entrada dos subprocessos (python -m …)
    dependencies.py   o composition root: monta as implementações e entrega aos use cases
```

Uma interface do `domain/interfaces/` é implementada ou em `infrastructure/repositories/` (se é
um repositório) ou em `infrastructure/implementations/` (todo o resto). A única exceção é um
Protocol privado (`_IFailableJobRepository`): detalhe de tipagem do único arquivo que o usa, mora
ao lado dele, mas também leva o `I`.

O `shared/` não é uma funcionalidade, e por isso tem três exceções: `domain/errors/` (os erros,
um por arquivo), `infrastructure/database/` (conexão e migrations, uma pasta de tecnologia) e
`infrastructure/filesystem/` (o layout de `data/` e a guarda de caminho); o `settings.py` fica
na raiz de `infrastructure/`.

## Regra de dependência

```
presentation → application → domain ← infrastructure
```

- `domain/` não importa nada de fora dele mesmo, exceto `shared/domain/` e o `domain/` de outra
  funcionalidade. Pode usar pandas (aqui o dado *é* o domínio); não pode usar SQLite, FastAPI,
  torch nem o sistema de arquivos.
- `application/` importa de `domain/`. Nunca da infraestrutura: um use case recebe os repositórios
  pelas interfaces do domínio.
- `infrastructure/` implementa as interfaces do `domain/` e é o único lugar que chama `ml/`.
- `presentation/` importa de `application/` e monta tudo (o *composition root*).
- **Entre funcionalidades, só se importa o `domain/` da outra.** Quando uma funcionalidade precisa
  de infraestrutura de outra (o dashboard precisa carregar o modelo treinado), ela usa uma interface
  declarada no `domain/` da dona, ligada no composition root.
- **A relação entre duas funcionalidades fica com quem tem a chave estrangeira.** A `problem_kc`
  aponta para `problem`, então quem junta problema e KC é `knowledge_components`, e não
  `assignments/problems`. Fazer o contrário andaria contra a seta e criaria um ciclo. Uma rota que
  mostra as duas coisas juntas pode morar em qualquer uma das duas `presentation/`, que monta peças
  de outras funcionalidades.
- **Uma sub-funcionalidade** (como `assignments/problems/`) é uma pasta com as quatro camadas
  próprias dentro de uma funcionalidade. Para as regras, ela conta como uma funcionalidade à parte.

Essas regras são verificadas pelo `import-linter` (contratos em `pyproject.toml`). Uma violação
reprova a verificação, então a regra não depende de lembrar dela. As convenções de pasta e de
nome das interfaces são verificadas por `src/api/architecture_test.py`, que roda com a suíte:

```bash
docker run --rm --security-opt label=disable -v "$PWD":/app -w /app edmkt-core:dev lint-imports
```

## Transações e regras

- Um use case que grava recebe um `IUnitOfWork` (`shared/application/interfaces/unit_of_work.py`):
  tudo dentro do `with` é gravado junto, ou nada é. A implementação SQLite fica na infraestrutura.
- Uma regra de negócio (`IBusinessRule`, em `shared/domain/interfaces/business_rule.py`) recebe
  no construtor as interfaces de repositório de que precisa, e `check(dto)` devolve a mensagem de
  recusa ou `None`. Os use cases de escrita estendem `WriteUseCase`, que roda todas as regras e
  acumula as recusas.
- Os erros do domínio (`NotFound`, `BusinessRuleViolation`, `AnotherJobRunning` e
  `IncompatibleTrainedModelError`, em `shared/domain/errors/`) não conhecem HTTP;
  `shared/presentation/http/error_handlers.py` os traduz para 404 e 409.

## Arquivos em disco

Tudo o que uma turma tem fora do banco fica sob o id dela, que nunca muda, e só
`shared/infrastructure/filesystem/data_layout.py` monta esses caminhos:

```
data/<classroom_id>/
  raw/<data-e-hora>_<nome-do-zip>/     o cru de cada envio
  cache/paths/<assignment_id>/         os AST paths já extraídos
  kc/<assignment_id>/                  as respostas do LLM da geração de KCs
  models/<assignment_id>/v<K>/         as versões de modelo treinadas
```

## Remoção

Remover é sempre soft delete: a linha fica, com a data da remoção em `deleted_at`, e só os
repositórios sabem disso. Toda leitura de um repositório devolve só as linhas ativas
(`deleted_at IS NULL`), então nenhum use case precisa lembrar do filtro. Hoje vale para `kc` e
`problem_kc`; uma tabela nova que ganhe remoção segue a mesma regra.

## Nomes

Seguem a [PEP 8](https://peps.python.org/pep-0008/) e dizem a intenção.

| O quê | Padrão | Exemplo |
|---|---|---|
| Arquivo | `snake_case`: a coisa principal + o papel | `start_training_use_case.py` |
| Classe | `PascalCase`: substantivo + sufixo do papel | `StartTrainingUseCase`, `StartTrainingDTO` |
| Interface (`Protocol`) | `I` + `PascalCase` | `IAssignmentRepository`, `ICodeDktTrainer` |
| Função e método | `snake_case`: verbo + objeto | `find_students_at_risk()` |
| Booleano | `is_` / `has_` / `can_` | `is_another_job_running()` |
| Constante | `UPPER_SNAKE` | `CODE_DKT_HYPERPARAMETERS` |

Sufixos de papel: `_entity`, `_rule`, `_repository` (a interface no domínio), `sqlite_…_repository`
(a implementação), `_use_case`, `_dto`, `_controller`, `_worker`.

O prefixo `I` não é da PEP 8 (a comunidade Python costuma nomear o Protocol só pela capacidade).
Ele está aqui por escolha: numa assinatura como `assignments: IAssignmentRepository`, deixa claro
que entra um contrato e não uma implementação, e forma o par com quem implementa
(`IAssignmentRepository` → `SqliteAssignmentRepository`). O arquivo não leva o `i_`: a pasta
`interfaces/` já diz o que ele é (`interfaces/assignment_repository.py`). O `LLMClient` do `ml/`
fica sem `I`: o `ml/` é biblioteca e não segue as convenções da `api/`.

## Comentários

- Só comentário `#`, nunca docstring. As rotas descrevem a si mesmas pelo `description=` do
  decorator do FastAPI.
- Uma linha por comentário, curta, em pt-BR, e só onde o *porquê* não é óbvio lendo o código.
- Sem travessão e sem dois-pontos. Dois-pontos só dentro de um trecho de código entre crases ou num
  pragma de ferramenta (`# noqa`, `# type: ignore`).
- O comentário faz sentido sozinho, sem apontar para outro documento.
- Nas migrations SQL vale o mesmo, com `--`.

O raciocínio completo das decisões não óbvias fica em [DECISIONS](DECISIONS.md). A regra é
verificada por `src/api/code_comments_test.py`, que roda com a suíte.

## Testes

O teste fica **ao lado do arquivo que testa**, com o sufixo `_test.py`:

```
start_training_use_case.py
start_training_use_case_test.py
```

- As fixtures compartilhadas ficam no `conftest.py` da raiz do repositório.
- **Os testes também respeitam as camadas.** Um teste ao lado de um use case importa só a própria
  camada e o domínio. Quando precisa da infraestrutura real (SQLite, disco), quem a monta é uma
  fixture em `tests/fixtures/<funcionalidade>.py`, que fica fora de `api/` e é registrada no
  `conftest.py` da raiz. Assim o `import-linter` vale para o teste como vale para o código.
- Em `tests/` ficam só o teste de regressão contra a execução de referência do TCC 1 (o sistema
  inteiro, com GPU e o CSEDM real), os dados de exemplo em `tests/data/` e as fixtures de
  `tests/fixtures/`.
- Tudo roda no container, nunca no host.

## Jobs em background

Treino e geração de KCs rodam em subprocess
(`python -m api.<funcionalidade>.presentation.workers.<…>_worker`), serializados pelo
`OneJobAtATimeLock`, uma linha no banco validada pela vida do PID do dono. O banco é o canal entre
os processos: o estado do job vive em `training_job` / `kc_job`.

## Frontend

`src/web/src/` segue a mesma ideia do backend, organizado por funcionalidade primeiro, com três
camadas de componente e uma fronteira de conhecimento entre elas.

```
app/          o casco: barra superior, menu em árvore, a tabela de rotas e o ErrorBoundary
components/
  ui/         primitivas sem domínio (Button, Card, Dialog, Tabs, Tooltip, StageList, RatioBar…)
  states/     os quatro estados de toda tela (carregando, erro, vazio, conteúdo)
  …           outros componentes de produto, como o PageHeader e o Breadcrumb
features/
  <funcionalidade>/
    api/        os hooks de dados (TanStack Query) e os tipos do DTO
    components/ os componentes que conhecem o domínio
    pages/      a página que entra na tabela de rotas
http/         o cliente (a via única de dados) e o schema.d.ts gerado do OpenAPI
lib/          funções puras transversais (formatação, rota por hash, caminhos das telas)
styles/       os tokens da linguagem visual
```

As funcionalidades têm o nome das do backend (`classrooms`, `assignments`, `mastery_dashboard`…), e
uma pasta só existe quando tem conteúdo. `assignments/` e `model_training/` hoje só têm `api/`.

### Rotas

O endereço carrega o contexto, como em `#/classrooms/1/assignments/2/analysis`. A tabela de
`app/routes.ts` casa o caminho com um padrão (`matchPath`, só ids inteiros) e passa os parâmetros à
página, e `lib/paths.ts` monta os caminhos. Nenhuma tela tem seletor de turma ou de exercício. O
menu lateral lista turma, exercício e as telas de cada exercício, e o `Breadcrumb` no topo de cada
tela mostra o mesmo caminho.

### Fronteiras

- `components/` não conhece nenhuma funcionalidade nem o `app/`. Recebe dados genéricos,
  `children` e a política de quem o usa (o texto do vazio, o que conta como vazio), nunca a decide.
- `lib/` e `http/` dependem só de `lib/` e `http/`.
- Uma funcionalidade nunca importa o `app/`.
- **Entre funcionalidades, só se importa o `api/` da outra** (os hooks e os tipos), nunca os
  componentes. É o espelho da regra do backend, em que se importa só o `domain/` da outra.

As quatro regras são verificadas por `src/web/architecture.test.ts`, que resolve cada import para o
arquivo real. O ESLint não serve aqui, porque com imports relativos `../../components/ui` e
`../../classrooms/components` têm a mesma forma.

### Composição, estado e effects

- Nenhum componente é definido dentro de outro (`react/no-unstable-nested-components` como erro).
- Um componente se decompõe por lógica, não por tamanho. Um subcomponente privado, sem estado e sem
  teste próprio fica no arquivo de quem o usa.
- Estado é o mínimo que não se calcula. Estados que se excluem viram um `status` só, e uma seleção
  guarda o id, nunca o objeto.
- `useEffect` só sincroniza com algo de fora do React. Hoje são o `showModal()` do `Dialog`, o
  aviso de `beforeunload` dos diálogos de job e o `localStorage` do menu. A rota lê o hash com
  `useSyncExternalStore`, sem effect.
- Um formulário nasce limpo por remontagem, nunca por effect de reset. O `Dialog` só renderiza o
  conteúdo aberto.
- Sem `useMemo`, `useCallback` ou `memo` defensivos.

### Linguagem visual

O que o app desenha (cores, tipografia, componentes, tabelas e gráficos) está em `docs/DESIGN.md`.
Aqui fica só como o CSS é escrito.

CSS puro, com os tokens de `styles/tokens.css` e um `.css` ao lado de cada componente. Nenhuma cor
é escrita no ponto de uso. Cada variante tem a sua situação de uso, escolhida por uma prop
`variant` que troca a classe, e uma variante sem uso não nasce. Barras e histogramas são CSS, e o
Chart.js desenha só a curva de perda do treino, lendo a cor do token na hora. As dicas de hover
usam o `Tooltip`, nunca o `title` nativo. A janela não rola, só o conteúdo, então a barra superior
e o menu ficam parados.

### Verificação

Tudo roda no container `web`.

```bash
docker compose run --rm web sh -c "npx tsc -b && npx eslint . && npx prettier --check . && npx vitest run"
```

Os tipos da api saem do OpenAPI com `npm run types`, com a api no ar, e o `schema.d.ts` nunca é
editado à mão. A regra dos comentários vale também aqui (só `//`, uma linha), verificada pelo mesmo
`src/api/code_comments_test.py`.
