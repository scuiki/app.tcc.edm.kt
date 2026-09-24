# Arquitetura do backend

Dois pacotes em `src/`:

- **`ml/`**: a ciência (Code-DKT, KCGen-KT, AUC, agregação de mastery). É uma biblioteca, como o
  torch: não conhece HTTP, banco nem disco da aplicação, e **nunca importa de `api/`**. É o que o
  teste de regressão contra o TCC 1 exercita.
- **`api/`**: a aplicação. Organizada **por funcionalidade primeiro**, com as camadas de clean
  architecture dentro de cada uma.

Os nomes seguem o [glossário](GLOSSARY.md).

## Funcionalidades

| Pasta | Responsabilidade |
|---|---|
| `api/assignments/` | `Classroom`, `Assignment` e o ciclo de `AssignmentStatus`. Todas as outras dependem dela |
| `api/classroom_import/` | Upload do ProgSnap2, validação, limpeza, checagem de treinabilidade |
| `api/knowledge_components/` | Gerar KCs com o LLM, editar e aprovar a Q-matrix |
| `api/model_training/` | Disparar e acompanhar o treino do Code-DKT, guardar os modelos |
| `api/mastery_dashboard/` | Mastery, recomendações e estatísticas pré-treino |
| `api/shared/` | O que todas usam: erros, base de use case, banco, trava, settings |

Toda funcionalidade tem as quatro pastas, mesmo que alguma fique com um arquivo só:

```
<funcionalidade>/
  domain/           entidades, regras de negócio, interfaces (Protocol) dos repositórios
  application/      use cases e DTOs
  infrastructure/   implementações SQLite, disco, LLM, torch
  presentation/     controllers HTTP (FastAPI) e workers (entrada dos subprocessos)
```

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

Essas regras são verificadas pelo `import-linter` (contratos em `pyproject.toml`). Uma violação
reprova a verificação, então a regra não depende de lembrar dela:

```bash
docker run --rm --security-opt label=disable -v "$PWD":/app -w /app edmkt-core:dev lint-imports
```

## Transações e regras

- Um use case que grava recebe um `UnitOfWork` (`shared/application/unit_of_work.py`): tudo dentro
  do `with` é gravado junto, ou nada é. A implementação SQLite fica na infraestrutura.
- Uma regra de negócio (`shared/domain/business_rule.py`) recebe no construtor as interfaces de
  repositório de que precisa, e `check(dto)` devolve a mensagem de recusa ou `None`. Os use cases de
  escrita estendem `WriteUseCase`, que roda todas as regras e acumula as recusas.
- Os erros do domínio (`NotFound`, `BusinessRuleViolation`, `AnotherJobRunning`) não conhecem HTTP;
  `shared/presentation/http/error_handlers.py` os traduz para 404 e 409.

## Nomes

Seguem a [PEP 8](https://peps.python.org/pep-0008/) e dizem a intenção.

| O quê | Padrão | Exemplo |
|---|---|---|
| Arquivo | `snake_case`: a coisa principal + o papel | `start_training_use_case.py` |
| Classe | `PascalCase`: substantivo + sufixo do papel | `StartTrainingUseCase`, `StartTrainingDTO` |
| Função e método | `snake_case`: verbo + objeto | `find_students_at_risk()` |
| Booleano | `is_` / `has_` / `can_` | `is_another_job_running()` |
| Constante | `UPPER_SNAKE` | `CODE_DKT_HYPERPARAMETERS` |

Sufixos de papel: `_entity`, `_rule`, `_repository` (a interface no domínio), `sqlite_…_repository`
(a implementação), `_use_case`, `_dto`, `_controller`, `_worker`.

## Testes

O teste fica **ao lado do arquivo que testa**, com o sufixo `_test.py`:

```
start_training_use_case.py
start_training_use_case_test.py
```

- As fixtures compartilhadas ficam no `conftest.py` da raiz do repositório.
- A única exceção é `tests/`: o teste de regressão contra a execução de referência do TCC 1 (o
  sistema inteiro, com GPU e o CSEDM real) e os dados de exemplo em `tests/data/`.
- Tudo roda no container, nunca no host.

## Jobs em background

Treino e geração de KCs rodam em subprocess (`python -m api.<funcionalidade>.presentation.<…>_worker`),
serializados pelo `OneJobAtATimeLock`, uma linha no banco validada pela vida do PID do dono. O banco
é o canal entre os processos: o estado do job vive em `training_job` / `kc_job`.
