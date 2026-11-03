# Plano de implementação do design v5

Documento para retomar o trabalho. Ele junta o contexto das iterações de design, o que o código tem
hoje e a separação inicial do trabalho em blocos de backend e de frontend. O plano de cada bloco
ainda vai ser discutido, e este arquivo é o ponto de partida dessa discussão, não o plano fechado.

Estado em 08/10/2026, com a base concluída pelo `FRONTEND_BASE_PLAN.md` e a tela Conceitos pelo
`CONCEPTS_SCREEN_PLAN.md`. A seção 9 registra as decisões da discussão de 30/09 e 01/10/2026 e a
ordem nova, que põe a fidelidade à literatura antes da base. O treino pela tela foi testado de ponta
a ponta pelo Leo em 08/10/2026, na turma 7 "Teste novo", em cerca de 2 min 20 s.

## 1. Contexto

Entre 29/09 e 08/10/2026 o design do app foi refeito em seis versões, todas no `main`.

| Versão | Commit | O que definiu |
|---|---|---|
| v1 | `f92ac2f` | A linguagem formal. Interface em cinza, raio 0, sombra só em cartão e diálogo, Public Sans na interface e Arial nos dados, componentes no estilo Carbon |
| v2 | `71814c9` | A organização da Análise, com a linha de fatos, as abas com Conceitos primeiro e a curva de aprendizagem |
| v3 | `ecd81e2` | Turmas e Turma, com a tabela de exercícios, os alunos da turma paginados e as execuções por dia |
| v4 | `57a6d87` | Conceitos, com a matriz problema × conceito e a origem do conceito, e os marcadores de modelo |
| v5 | `876e740` | Importar dados, com os requisitos do pacote, e o fim da barra fixa no app |
| v6 | `5691233` | A tela Conceitos, com a matriz problema × conceito, o enunciado, o aviso de reabrir a aprovação e a origem do conceito empilhada |

A fonte da verdade são quatro arquivos, e este documento não repete o que eles dizem.

- `docs/DESIGN.md` tem as regras, os componentes por nome de token, os ícones e a organização das
  cinco telas.
- `docs/design/design-system-v6.html` mostra cada peça e tem os valores (hex, medidas, sombras).
  Abre direto no navegador.
- `docs/DECISIONS.md`, na seção Frontend, tem o porquê de cada escolha.
- `docs/GLOSSARY.md` tem os nomes novos, que valem para o código (`GeneratedByML`, `GeneratedByLLM`,
  `LearningCurve`, `SampledSolution`, `AssignmentOverview`, `ClassroomStudentSummary`, `DailyRuns`,
  `ActivityEvent`, `PackageRequirement`).

As maquetes das iterações de design (links em Versões, no fim do `DESIGN.md`) são só registro.
Várias opções delas foram descartadas depois, então elas não servem de referência para implementar.

## 2. O código hoje

### Frontend

A base do design v5 está feita pelo `FRONTEND_BASE_PLAN.md`, concluído em 08/10/2026. O `tokens.css`
tem as cores, as sombras, o raio 0 e a tipografia da v5, os componentes que já existiam seguem a
linguagem nova, e as tabelas da Análise e de Turmas usam a `DataTable`. A tela Conceitos foi refeita
em seguida, pelo `CONCEPTS_SCREEN_PLAN.md`, e as outras quatro telas ainda têm a organização
anterior ao design. A importação usa o `PageActionBar`, a barra fixa no rodapé, que sai com ela.

Os componentes compartilhados estão em `src/web/src/components/` (`Breadcrumb`, `FactsLine`,
`FileDropZone`, `GeneratedByLLM`, `GeneratedByML`, `OutcomeMessage`, `PageActionBar`, `PageHeader`,
`states`) e em `src/web/src/components/ui/` (`Badge`, `Button`, `Card`, `CodeBlock`, `DataTable`,
`Dialog`, `Histogram`, `InfoHint`, `RatioBar`, `SearchField`, `SelectField`, `SortableHeader`,
`StageList`, `Tabs`, `TextField`, `Tooltip`). O menu e a barra superior estão em `src/web/src/app/`.
As dependências relevantes são Chart.js 4.5.1 com react-chartjs-2 5.3.1 e lucide-react 1.21.0, que
já têm tudo o que o design pede.

### Backend

As rotas de hoje, agrupadas por funcionalidade.

| Funcionalidade | Rotas |
|---|---|
| classrooms | `GET/POST /classrooms`, `PUT/DELETE /classrooms/{id}` |
| assignments | `GET /assignments`, `GET /assignments/{id}/problems`, `GET /assignments/{id}/problems/knowledge-components` |
| classroom_import | `POST /classroom-imports`, `POST /classroom-imports/process` |
| knowledge_components | geração (`POST /knowledge-components/generation-jobs`, `GET .../generation-jobs/{job_id}`), listar, criar, renomear, remover, `POST /approve`, ligar e desligar conceito de problema, e a origem do conceito (`GET /knowledge-components/{kc_id}/origin`) |
| model_training | `POST /training-jobs`, `GET /training-jobs/{id}`, `GET /training-jobs/{id}/loss-history` |
| mastery_dashboard | `GET /mastery-dashboard/{assignment_id}/submission-statistics`, `.../mastery`, `.../students`, `.../students/{student_id}` |

O que já sai da API e as telas usam hoje inclui a contagem de alunos e problemas da turma e a
situação dela, a lista de exercícios com nome e situação, as estatísticas por problema e por
conceito, o enunciado e a contagem de execuções corretas de cada problema com os conceitos dele e a
data da extração, a origem de cada conceito, o domínio com a versão e a data do modelo, a lista de
alunos e o detalhe de um aluno, e o envio do pacote com as tabelas encontradas (`raw_dir`,
`main_tables`, `code_snapshots`).

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
soluções amostradas gravadas na extração. A rota e o diálogo da origem do conceito saíram com a tela
Conceitos, pelo `CONCEPTS_SCREEN_PLAN.md`, em 08/10/2026.

**B2. Conceito editado pelo professor.**
O marcador `GeneratedByLLM` some do nome do conceito quando o professor o renomeia, e um conceito
criado em "Novo conceito" também não é do modelo. A tabela `kc` não registra o renomear hoje,
então entra uma coluna, o que pede uma migração do banco. A rota de mesclar
(`POST /knowledge-components/merge`) sai, porque o design tirou o mesclar. Depende disso a tela
Conceitos. Em 08/10/2026, o B2 passou ao `CONCEPTS_SCREEN_PLAN.md`, que fez a coluna `updated_at`
do `kc` e a saída do mesclar inteiro.

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
da extração. O que já existe (alunos, problemas, conceitos, versão e data do modelo) continua. A
parte da Conceitos, a data da extração, entrou pelo `CONCEPTS_SCREEN_PLAN.md`.

**B9. Requisitos do pacote.**
O envio devolve as tabelas encontradas, mas o formato ProgSnap2 v6 (as colunas obrigatórias) só é
conferido no processamento. Para o requisito "Formato ProgSnap2 v6" ganhar o visto antes de
processar, o envio passa a ler o cabeçalho da tabela de eventos. O tamanho já é conferido no front,
antes de enviar. Depende disso a tela Importar dados.

## 4. Blocos de frontend

**Estado em 08/10/2026.** O F1, a migração dos componentes que já existiam e o F3 estão feitos pelo
`FRONTEND_BASE_PLAN.md`, e o `GeneratedByML` já existe. A tela Conceitos, pelo
`CONCEPTS_SCREEN_PLAN.md`, fez do F2 o `GeneratedByLLM`, o bloco de código, as ações na faixa das
abas e a linha de fatos, com as variantes novas de `Dialog`, `Tabs`, `Tooltip` e `DataTable`. Do F2
ficam com as outras telas o indicador de passos, a paginação, a lista de requisitos e o cartão com
título com ícone e rodapé com ações. O menu que recolhe abaixo de 900px fica para uma etapa própria,
depois da tela Conceitos.

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
`GeneratedByML` (feito na base), o `GeneratedByLLM`, o indicador de passos (hoje
`ImportSteps`, dentro da importação), a paginação, o bloco de código com abas e a lista de
requisitos. O `PageActionBar` sai. Não depende de backend.

**F3. Tabelas.**
Cabeçalho e linhas de 32px, rótulo que trunca com o texto inteiro no hover, fio entre as linhas em
todas as tabelas, histograma sem eixo e barras quadradas, tudo em `--font-data`. Não depende de
backend.

**F4. Gráficos.**
A curva de aprendizagem com dois eixos (linha e barras) e a figura de execuções por dia. Dependem
de B3 e de B6. O Chart.js saiu em 03/11/2026 junto com a curva de perda do treino, então a
biblioteca destas figuras volta com uma decisão nova (`docs/REMOVED_FEATURES.md`).

**F5. As telas.**

| Tela | O que muda | Blocos de backend |
|---|---|---|
| Análise | Linha de fatos, abas com Conceitos primeiro, vista Tabela e Curva de aprendizagem, sem cabeçalho agrupado | B3, B8 |
| Turmas | Linha de fatos, Nova turma como primário, atividade recente | B7 |
| Turma | Cabeçalho com Importar dados, figura de execuções por dia, abas Exercícios e Alunos | B4, B5, B6, B8 |
| Conceitos | Feita em 08/10/2026, pelo `CONCEPTS_SCREEN_PLAN.md`. Título do exercício, linha de fatos, abas com a matriz e os problemas, origem do conceito, sem mesclar | B1, B2, B8 |
| Importar dados | Requisitos do pacote, caixa do pacote de altura fixa, ações no rodapé do cartão, resultado com a tabela de exercícios da Turma | B4, B9 |

## 5. Dependências entre os blocos

F1, F2 e F3 não dependem de backend e andaram primeiro, na base concluída em 08/10/2026. Cada tela
de F5 espera os blocos de backend da tabela acima, e F4 espera B3 e B6. B4 serve a duas telas. B1 é
o único bloco com consequência científica e custo de cota, e a nova extração pede cuidado com o
A439.

## 6. Pendências conhecidas

- **A amostragem do KCGen-KT** (B1), que mandava uma solução por problema ao LLM em vez de cinco,
  corrigida pelo `KCGEN_KT_PLAN.md`. A descrição deduzida pelo LLM deixou de ser gravada e saiu do
  banco, das rotas e da tela com a tela Conceitos, que mostra no lugar dela o enunciado, que é
  opcional.
- **A validação da tela Conceitos.** A tela está feita pelo `CONCEPTS_SCREEN_PLAN.md`, sem a
  descrição do problema nem a tentativa de cada solução, que saíram do KCGen-KT, e com uma matriz
  pensada para 25 conceitos, quando o desenho antigo era para 15. Faltam a revisão independente da
  tela e a validação do Leo. O `DESIGN.md` e a página `docs/design/design-system-v6.html` descrevem
  a tela nova.
- **O 409 de modelo antigo na Análise.** A rota do domínio responde 409 quando precisa carregar um
  modelo de formato antigo (`IncompatibleTrainedModelError`), e a Análise ignora o erro
  (`AnalysisCard.tsx:39`, `:60`, `:74`). As colunas do modelo ficam vazias, sem aviso. Fica para a
  tela Análise.
- **As extrações das turmas antigas.** As da turma CSEDM Spring 2019 e da turma 5, de 21/06 e
  25/09, não têm o nome gerado nem as soluções amostradas, os KCs candidatos e os trechos. Na tela
  Conceitos refeita, os conceitos delas ficam sem as estrelas, e a origem do conceito mostra todo
  vínculo como feito pelo professor. Sem solução amostrada, ela mostra também, em todo problema, a
  frase do problema sem solução ("Ninguém acertou este problema, então o modelo não leu nenhuma
  solução dele."), mesmo nos problemas com acertos. Nenhum código trata o caso, e o dado errado
  nessas turmas é aceito de propósito pela decisão X do `CONCEPTS_SCREEN_PLAN.md`. O Leo decidiu
  apagar as duas turmas e fazer uma nova extração pela aplicação (seção 9).
- **O detalhe do aluno lento.** Cerca de 1,3 s por chamada, porque recarrega o recorte do exercício a
  cada GET.

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
- **Comentários só com `#`, `//` ou o `/* */` do CSS**, de uma linha, sem travessão nem dois-pontos,
  verificados por `src/api/code_comments_test.py`. O porquê longo vai para o `DECISIONS.md`.
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
  a reimportação estar pronta. Em 08/10/2026, com a tela Conceitos, o Leo decidiu apagar a turma
  CSEDM Spring 2019 e a turma 5. A CSEDM Spring 2019 tem o único exercício treinado do banco, então
  sai só depois do treino do A439 da turma nova (seção "Depois do plano, com o Leo" do
  `CONCEPTS_SCREEN_PLAN.md`).
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
   aprovado e concluído em 08/10/2026, e depois as telas, uma por vez (Conceitos, Análise, Turma,
   Importar dados e Turmas), cada uma com o seu backend. A Conceitos seguiu o
   `CONCEPTS_SCREEN_PLAN.md`, aprovado e executado em 08/10/2026.
