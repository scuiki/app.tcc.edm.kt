# Plano de implementação do design v5

Documento para retomar o trabalho. Ele junta o contexto das iterações de design, o que o código tem
hoje e a separação inicial do trabalho em blocos de backend e de frontend. O plano de cada bloco
ainda vai ser discutido, e este arquivo é o ponto de partida dessa discussão, não o plano fechado.

Estado em 30/09/2026, com a base em andamento desde 08/10/2026 pelo `FRONTEND_BASE_PLAN.md`. A
seção 9 registra as decisões da discussão de 30/09 e 01/10/2026 e a ordem nova, que põe a fidelidade
à literatura antes da base.

## 1. Contexto

Entre 29 e 30/09/2026 o design do app foi refeito em cinco versões, todas no `main` e no GitHub.

| Versão | Commit | O que definiu |
|---|---|---|
| v1 | `bd96300` | A linguagem formal. Interface em cinza, raio 0, sombra só em cartão e diálogo, Public Sans na interface e Arial nos dados, componentes no estilo Carbon |
| v2 | `91ec267` | A organização da Análise, com a linha de fatos, as abas com Conceitos primeiro e a curva de aprendizagem |
| v3 | `129959a` | Turmas e Turma, com a tabela de exercícios, os alunos da turma paginados e as execuções por dia |
| v4 | `8da55ed` | Conceitos, com a matriz problema × conceito e a origem do conceito, e os marcadores de modelo |
| v5 | `fdaaadc` | Importar dados, com os requisitos do pacote, e o fim da barra fixa no app |

A fonte da verdade são quatro arquivos, e este documento não repete o que eles dizem.

- `docs/DESIGN.md` tem as regras, os componentes por nome de token, os ícones e a organização das
  cinco telas.
- `docs/design/design-system-v5.html` mostra cada peça e tem os valores (hex, medidas, sombras).
  Abre direto no navegador.
- `docs/DECISIONS.md`, na seção Frontend, tem o porquê de cada escolha.
- `docs/GLOSSARY.md` tem os nomes novos, que valem para o código (`GeneratedByML`, `GeneratedByLLM`,
  `LearningCurve`, `SampledSolution`, `AssignmentOverview`, `ClassroomStudentSummary`, `DailyRuns`,
  `ActivityEvent`, `PackageRequirement`).

As maquetes das iterações de design (links em Versões, no fim do `DESIGN.md`) são só registro.
Várias opções delas foram descartadas depois, então elas não servem de referência para implementar.

## 2. O código hoje

### Frontend

O `tokens.css` já tem as cores, as sombras e o raio 0 da v5. A tipografia ainda é a anterior, com a
Open Sans carregada do Google Fonts no `index.html`, `--font-mono` e `--font-table` (Arial só nas
tabelas da Análise). As telas têm a organização anterior ao design, e
a importação e os conceitos usam o `PageActionBar`, a barra fixa no rodapé.

Componentes que existem e mudam na migração estão em `src/web/src/components/` (`Breadcrumb`,
`FileDropZone`, `OutcomeMessage`, `PageActionBar`, `PageHeader`, `states`) e em
`src/web/src/components/ui/` (`Badge`, `Button`, `Card`, `Dialog`, `Histogram`, `InfoHint`,
`RatioBar`, `SearchField`, `SelectField`, `SortableHeader`, `StageList`, `Tabs`, `TextField`,
`Tooltip`). O menu e a barra superior estão em `src/web/src/app/`. As dependências relevantes são
Chart.js 4.5.1 com react-chartjs-2 5.3.1 e lucide-react 1.21.0, que já têm tudo o que o design pede.

### Backend

As rotas de hoje, agrupadas por funcionalidade.

| Funcionalidade | Rotas |
|---|---|
| classrooms | `GET/POST /classrooms`, `PUT/DELETE /classrooms/{id}` |
| assignments | `GET /assignments`, `GET /assignments/{id}/problems`, `GET /assignments/{id}/problems/knowledge-components` |
| classroom_import | `POST /classroom-imports`, `POST /classroom-imports/process` |
| knowledge_components | geração (`POST /knowledge-components/generation-jobs`, `GET .../generation-jobs/{job_id}`), criar, renomear, remover, `POST /merge`, `POST /approve`, ligar e desligar conceito de problema |
| model_training | `POST /training-jobs`, `GET /training-jobs/{id}`, `GET /training-jobs/{id}/loss-history` |
| mastery_dashboard | `GET /mastery-dashboard/{assignment_id}/submission-statistics`, `.../mastery`, `.../students`, `.../students/{student_id}` |

O que já sai da API e as telas usam hoje inclui a contagem de alunos e problemas da turma e a
situação dela, a lista de exercícios com nome e situação, as estatísticas por problema e por
conceito, o domínio com a versão e a data do modelo, a lista de alunos e o detalhe de um aluno, e o
envio do pacote com as tabelas encontradas (`raw_dir`, `main_tables`, `code_snapshots`).

## 3. Blocos de backend

Cada bloco diz o que falta, por que, quais telas dependem dele e o que ainda está em aberto.

**B1. Correção da amostragem do KCGen-KT e origem do conceito (substituído pelo
`KCGEN_KT_PLAN.md`).** O `kcgen_kt_generator.py` filtra só as execuções corretas antes de chamar
`select_sample_solutions`, e a amostragem das soluções, que conta as tentativas pelas execuções
anteriores do aluno, passa a ver todo aluno acertando de primeira. O LLM recebe uma solução por
problema em vez de até cinco diversas. O TCC 1 (`load_correct_samples`, notebook `03b`) contava com
todas as execuções, e atribuía isso ao Duan. A correção é passar à amostragem as execuções do
problema. Junto com ela, a extração passa a gravar as soluções amostradas (`SampledSolution`, pela
execução escolhida, `submission_id`), e uma rota nova devolve as soluções de cada problema para o
diálogo da origem do conceito. Depende disso a tela Conceitos. Em aberto: a nova extração gasta cota
da assinatura, porque o prompt muda. O Assignment 439 está treinado com os conceitos antigos e não
tem descrição dos problemas, e extraí-lo de novo pede descongelar os conceitos e re-treinar. Revisto
em 30/09/2026 (seção 9), as faixas de tentativas não são do Duan, que agrupa os embeddings CodeBERT
das soluções corretas e amostra uma por grupo, e o prompt do app não é o do paper. O B1 passa a
depender da etapa de fidelidade do KCGen-KT. Em 04/10/2026, o B1 foi substituído pelo
`KCGEN_KT_PLAN.md`, que leva ao código as decisões do KCGen-KT do `DEVELOPMENT.md`, inclusive as
soluções amostradas gravadas na extração. A rota e o diálogo da origem do conceito ficam com a tela
Conceitos.

**B2. Conceito editado pelo professor.**
O marcador `GeneratedByLLM` some do nome do conceito quando o professor o renomeia, e um conceito
criado em "Novo conceito" também não é do modelo. A tabela `kc` não registra isso hoje, então entra
uma coluna, o que pede uma migração do banco. A rota de mesclar (`POST /knowledge-components/merge`)
sai, porque o design tirou o mesclar. Depende disso a tela Conceitos.

**B3. Curva de aprendizagem.**
Rota nova com a taxa de erro por oportunidade de cada conceito e os alunos que chegaram a cada uma,
com o corte em 10% da turma (`LearningCurve`). Sai das execuções e dos vínculos problema × conceito,
sem modelo. Depende disso a aba Conceitos da Análise.

**B4. Resumo dos exercícios.**
Rota nova (ou ampliação de `GET /assignments`) com o período, os alunos que participaram, as
execuções e a taxa de acerto de cada exercício (`AssignmentOverview`). Dependem disso a aba
Exercícios da Turma e o resultado da importação.

**B5. Alunos da turma.**
Rota nova, paginada de 10 em 10 e com busca pelo identificador, com a linha de cada aluno na turma
(`ClassroomStudentSummary`), inclusive o domínio médio nos exercícios treinados. Depende disso a aba
Alunos da Turma.

**B6. Execuções por dia.**
Rota nova com as execuções da turma por dia, ou por semana acima de cerca de 120 dias (`DailyRuns`),
e as janelas de cada exercício. A importação passa a ler o `ServerTimezone` do ProgSnap2 para o dia
ser o do fuso do dado, e hoje ela grava tudo em UTC. Depende disso a figura da Turma.

**B7. Atividade recente.**
Rota nova com os eventos (`ActivityEvent`) turma criada, dados importados, conceitos extraídos e
modelo treinado. Turma, extração e treino já têm datas no banco (`classroom`, `kc_job`,
`model_artifact`). A importação não tem registro próprio, e o evento sai do `created_at` dos
exercícios ou de um registro novo. Depende disso a tela Turmas.

**B8. Números das linhas de fatos.**
A linha de fatos de cada tela pede números que ainda não saem da API. A Análise pede o total de
execuções do exercício, a Turma pede o total de exercícios e de execuções, e Conceitos pede a data
da extração. O que já existe (alunos, problemas, conceitos, versão e data do modelo) continua.

**B9. Requisitos do pacote.**
O envio devolve as tabelas encontradas, mas o formato ProgSnap2 v6 (as colunas obrigatórias) só é
conferido no processamento. Para o requisito "Formato ProgSnap2 v6" ganhar o visto antes de
processar, o envio passa a ler o cabeçalho da tabela de eventos. O tamanho já é conferido no front,
antes de enviar. Depende disso a tela Importar dados.

## 4. Blocos de frontend

**F1. Tokens e fundamentos.**
O `tokens.css` passa aos tokens planejados no `DESIGN.md` (`--color-primary`, os tokens de modelo,
`--color-observed`, `--font-data`, `--font-code`, raio 0, as três sombras), e saem
`--color-accent*`, `--color-bar-*`, `--font-mono` e `--font-table`. A Public Sans substitui a Open
Sans no `index.html`. Não depende de backend.

**F2. Componentes base.**
Os componentes existentes passam à linguagem v5, e entram os novos. Existentes que mudam incluem
botão, etiqueta com ícone, cartão com título com ícone e rodapé com ações, abas com espaço para
ações, busca e vista, campo, dica com ?, balão com ícone, os estágios em azul nos dois diálogos, o
estado vazio, a mensagem de resultado, o menu com os pontos e recolhível abaixo de 900px, a barra
superior com o capelo preto, o caminho e o cabeçalho com a etiqueta e a linha de fatos. Novos são o
`GeneratedByML` (hoje `EstimatedMark`), o `GeneratedByLLM`, o indicador de passos (hoje
`ImportSteps`, dentro da importação), a paginação, o bloco de código com abas e a lista de
requisitos. O `PageActionBar` sai. Não depende de backend.

**F3. Tabelas.**
Cabeçalho e linhas de 32px, rótulo que trunca com o texto inteiro no hover, fio entre as linhas em
todas as tabelas, histograma sem eixo e barras quadradas, tudo em `--font-data`. Não depende de
backend.

**F4. Gráficos.**
A curva de aprendizagem com dois eixos (Chart.js, linha e barras) e a figura de execuções por dia. A
curva de perda do treino passa às cores e à fonte novas. Dependem de B3 e de B6.

**F5. As telas.**

| Tela | O que muda | Blocos de backend |
|---|---|---|
| Análise | Linha de fatos, etiqueta ao lado do título, abas com Conceitos primeiro, vista Tabela e Curva de aprendizagem, sem cabeçalho agrupado | B3, B8 |
| Turmas | Linha de fatos, Nova turma como primário, tabela em Arial, atividade recente | B7 |
| Turma | Cabeçalho com Importar dados, figura de execuções por dia, abas Exercícios e Alunos | B4, B5, B6, B8 |
| Conceitos | Título do exercício, linha de fatos, abas com a matriz e os problemas, origem do conceito, sem mesclar | B1, B2, B8 |
| Importar dados | Requisitos do pacote, caixa do pacote de altura fixa, ações no rodapé do cartão, resultado com a tabela de exercícios da Turma | B4, B9 |

## 5. Dependências entre os blocos

F1, F2 e F3 não dependem de backend e podem andar primeiro, em paralelo com o backend. Cada tela
de F5 espera os blocos de backend da tabela acima, e F4 espera B3 e B6. B4 serve a duas telas. B1 é
o único bloco com consequência científica e custo de cota, e a nova extração pede cuidado com o
A439.

## 6. Pendências conhecidas

- **A amostragem do KCGen-KT** (B1), que mandava uma solução por problema ao LLM em vez de cinco,
  corrigida pelo `KCGEN_KT_PLAN.md`. A descrição deduzida pelo LLM deixou de ser gravada, e a tela
  Conceitos troca a descrição pelo enunciado, que é opcional.
- **O desenho da tela Conceitos ainda traz a descrição do problema e a tentativa de cada solução**,
  que saíram do KCGen-KT. Está no `DESIGN.md` e na página `docs/design/design-system-v5.html`, na
  origem do conceito, na dica do número do problema, na aba Problemas e nos exemplos do marcador
  `GeneratedByLLM`. Quando a tela for refeita, entram no lugar o enunciado, os trechos de cada
  conceito e as justificativas traduzidas. A matriz problema × conceito foi pensada para 15
  conceitos, e o A439 agora tem 25.
- **O contrato do import-linter quebrado.** Conferido em 30/09/2026, o teste
  `sqlite_kc_generation_job_repository_test` importa as infraestruturas de `assignments` e de
  `classrooms`, o que o contrato de `knowledge_components` não permite. O comando que funciona é o
  do `README.md`. O do `ARCHITECTURE.md` está desatualizado, porque a imagem não traz o
  `lint-imports`.
- **O detalhe do aluno lento.** Cerca de 1,3 s por chamada, porque recarrega o recorte do exercício a
  cada GET.
- **O treino pela tela** nunca foi testado de ponta a ponta com um treino real, porque o treino
  congela os conceitos do exercício.

## 7. Perguntas para a discussão do plano

1. **A ordem.** O frontend (F1 a F3) primeiro, com as telas nos dados de hoje, e o backend depois?
   O backend primeiro? Ou tela por tela, cada uma com o seu backend?
2. **O tamanho de cada etapa.** Uma etapa por bloco, por tela, ou menores, e um commit por etapa ou
   por grupo?
3. **A nova extração e o A439.** Extrair de novo todos os exercícios depois de B1? Re-treinar o A439
   com os conceitos novos ou deixá-lo como está?
4. **Execuções por dia.** Chart.js, como as outras curvas, ou SVG próprio, e quando a figura entra,
   já que é a peça mais cara?
5. **A verificação.** Como cada etapa é conferida antes de seguir. Testes no container, capturas
   pelo protocolo de depuração e a revisão do Leo tela por tela, como nas iterações de design.
6. **O que fica para depois.** Algum bloco pode ficar fora da primeira leva, como a atividade
   recente ou a figura de execuções por dia?

## 8. Regras de trabalho

- **Discutir, planejar, aprovar e executar.** O Leo sinaliza quando a discussão acabou, o plano é
  apresentado e só é executado com a aprovação dele. Subagentes despachados na execução já trabalham
  sob o plano aprovado.
- **Dependências só no container**, nunca npm ou pip no host. Os testes do front rodam no container
  `web` e os do backend na imagem `edmkt-core:dev`, com os comandos do `README.md` e da seção
  Verificação do `ARCHITECTURE.md`.
- **Conferir sem escrever.** A tela real é conferida pelo Chrome sem janela, com o protocolo de
  depuração, sem clicar em nada que grave. Extração e treino gastam cota ou congelam conceitos, e só
  rodam com o Leo. A autorização de 04/10/2026 valeu só para as chamadas do `KCGEN_KT_PLAN.md`, que
  terminaram na etapa 7.
- **O glossário antes do código.** Um nome novo entra no `GLOSSARY.md` antes de entrar no código, e
  os nomes da seção 1 já estão lá.
- **Comentários só com `#` ou `//`**, de uma linha, sem travessão nem dois-pontos, verificados por
  `src/api/code_comments_test.py`. O porquê longo vai para o `DECISIONS.md`.
- **O KCGen-KT segue as decisões do `DEVELOPMENT.md`**, e o código cumpre as linhas 1 a 28 desde a
  etapa 8 do `KCGEN_KT_PLAN.md`. A linha 29, a comparação do KCGen-KT com o paper, espera a
  anotação do A439. O teste de regressão dele refaz a extração de referência do A439 a partir do
  cache gravado, e uma mudança no método só entra com uma decisão registrada no `DEVELOPMENT.md`.
  A extração dos outros quatro exercícios da CSEDM gasta cota e sai pela aplicação, com o Leo.
- **O Code-DKT segue as decisões do `DEVELOPMENT.md`.** O código as cumpre desde o fim do
  `CODE_DKT_PLAN.md`. Uma mudança no método só entra com uma decisão registrada no `DEVELOPMENT.md`.
  O teste de regressão detecta mudança de comportamento do código, com as dez seeds do A439 numa
  tolerância de ±0,1 ponto em torno da média de referência, 0,7278. A comparação com o paper é o
  teste `literature`, que registra o resultado e não falha pelos números.

## 9. Decisões de 30/09 e 01/10/2026

A discussão das perguntas da seção 7 fechou estes pontos.

- **A reimportação da CSEDM.** A CSEDM é importada de novo, numa turma separada da
  CSEDM Spring 2019, em vez de descongelar os conceitos do A439. A turma CSEDM Spring 2019 fica até
  a reimportação estar pronta.
- **Uma tela por vez.** As telas saem uma a uma, cada uma com o seu backend, revisada pelo Leo antes
  da próxima.
- **A figura de execuções por dia e o `ServerTimezone`** ficam para a segunda leva. O
  `ServerTimezone` da CSEDM é `0` ou `UTC` nas 201.570 linhas, então ler o fuso não muda nada com o
  dado do TCC.
- **A fidelidade à literatura vem antes da base.** A conferência com os papers mostrou que o
  Code-DKT do app é fiel ao TCC 1, mas só no essencial ao Shi, e que o KCGen-KT do app não segue o
  Duan na amostragem das soluções nem nos prompts. O Leo decidiu adequar os dois antes de mexer na
  base, revendo os papers seção por seção. As decisões e o porquê ficam no `DEVELOPMENT.md`.

A ordem nova é esta.

1. O Code-DKT, pelo `CODE_DKT_PLAN.md`, decidido e aprovado em 01/10/2026, e já no código.
2. O KCGen-KT, revisto contra o paper (Duan et al., 2025, e a versão publicada no ACL 2026) em 02
   e 03/10/2026, e levado ao código pelo `KCGEN_KT_PLAN.md`, aprovado em 04/10/2026. Ele substitui
   a correção do B1.
3. A reimportação da CSEDM, feita em 06/10/2026 na turma "CSEDM CodeWorkout, referência do
   KCGen-KT", e a extração do A439, na etapa 7 do `KCGEN_KT_PLAN.md`. Os outros quatro exercícios
   saem pela aplicação, e o treino vem depois da aprovação dos conceitos, uma vez só, com os dois
   métodos prontos.
4. A base (F1, a migração dos componentes que já existem e F3), pelo `FRONTEND_BASE_PLAN.md`,
   aprovado em 08/10/2026, e depois as telas, uma por vez (Conceitos, Análise, Turma, Importar
   dados e Turmas), cada uma com o seu backend.
