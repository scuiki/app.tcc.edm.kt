# Plano da tela Conceitos

Leva ao código a tela Conceitos refeita, a primeira das telas depois da base do front v5
(`FRONTEND_BASE_PLAN.md`), com o backend que ela pede. As decisões foram fechadas com o Leo em
08/10/2026, sobre a maquete publicada em https://claude.ai/artifact/PNNMqut5upVnbYG6vSWxkf. O Leo
aprovou o plano no mesmo dia e autorizou a execução direta de todas as etapas, inclusive a recriação
da api, e valida o código e a tela no fim. O porquê das decisões entra no `DECISIONS.md` na etapa
0, e este documento diz como e em que ordem elas entram no código.

## Escopo

Entram as decisões de A a X. No backend, a saída do mesclar, o `updated_at` do `kc` com o
marcador de gerado, a regra do Aprovar, o conceito novo com ao menos um problema, a rota da tela
com o enunciado, a contagem de execuções corretas e a data da extração, a saída da descrição e a
rota da origem do conceito. No front, o cabeçalho com a linha de fatos, o cartão com as abas, a
matriz com a ordem fixa, a aba Problemas, o Novo conceito, o Aprovar na faixa das abas, o aviso de
reabrir a aprovação, a origem do conceito e os estados treinado e pronto para conceitos, com as
peças que eles pedem (`GeneratedByLLM`, `FactsLine`, `CodeBlock` e as variantes de `Dialog`,
`Tabs`, `Tooltip` e `DataTable`). Nos documentos, o registro, a página de referência v6 e o
fechamento.

Ficam de fora, cada um com quem fica.
- Tela Análise. O 409 de modelo antigo (R), a linha de fatos dela (o resto do B8) e o "Problema N"
  repetido em cada linha da aba Problemas dela (`ProblemsTable.tsx:99`).
- Tela Importar dados. O `PageActionBar`, que a importação ainda usa
  (`ClassroomImportFlow.tsx:86`, `:125`) e que sai com ela.
- Depois da Conceitos, numa etapa própria. O menu que recolhe abaixo de 900px (decisão A do
  `FRONTEND_BASE_PLAN.md`).
- Com o Leo, depois do plano. A aprovação e o treino do A439 da turma 6, a exclusão das turmas
  antigas e a nova extração (seção "Depois do plano, com o Leo"). A recriação da api entra depois
  da etapa 6 (W).
- Fora desta rodada. As setas do teclado nas abas, que a maquete tem e o app não, o balão que só
  abre quando o texto corta, as organizações B e C da origem e um tratamento das extrações antigas
  na origem (X). O método do KCGen-KT não muda (Q), nem o prompt da tradução.

## Decisões fechadas com o Leo

As de A a H já estavam decididas no desenho e só faltava implementar. As de I a X são desta rodada.

- A. Cabeçalho. O título é o nome do exercício, com a etiqueta de situação ao lado e a linha de
  fatos abaixo, com problemas, conceitos, "extraídos em <data>" e quantos problemas estão sem
  conceito, em vermelho com `circle-alert` quando houver, ou "nenhum problema sem conceito".
- B. Cartão com as abas "Conceitos por problema" (`blocks`, a matriz) e "Problemas" (`file-code`).
  Novo conceito (secundário compacto) e Aprovar conceitos (primário compacto) ficam à direita das
  abas, só na aba da matriz.
- C. Matriz. Conceitos nas linhas e problemas nas colunas, em ordem numérica. A célula de 20px fica
  preenchida em `--color-text` quando ligada, a recorrência fica à direita, a última linha traz os
  conceitos por problema e as ações são lupa, lápis e lixeira, nessa ordem. O clique liga e desliga
  com as regras de hoje. Desliga direto, confirma quando o conceito sairia do exercício e recusa
  quando o problema ficaria sem conceito.
- D. Treinado. A matriz é só consulta, com as células em `--color-observed`, só a lupa e sem Novo
  conceito nem Aprovar.
- E. Pronto para conceitos. O cartão é o estado vazio com os blocos e um único "Extrair conceitos",
  e o `ExtractionDialog` de hoje fica, com os cinco estágios. statistics_only fica com o estado
  vazio de hoje.
- F. Mesclar sai inteiro, com a rota, o caso de uso, o `move_bindings`, o diálogo e os testes. Saem
  também o `ProblemsCard`, o `KnowledgeComponentsCard` e o `ApprovalBar`. Ficam o
  `ExtractionDialog`, os diálogos de renomear, remover e desligar e o `LeavesProblemEmpty`.
- G. `GeneratedByLLM`, componente novo em `components/`, irmão do `GeneratedByML`. Estrelas
  `sparkles` em `--color-model-strong` sobre círculo `--color-model-soft`, com a dica "Gerado pelo
  modelo de linguagem", no fim do texto (20px, e 24px num título) ou antes do rótulo de seção.
- H. Bloco de código com abas, componente novo. `--font-code` sobre `--color-surface-subtle`,
  numeração em `--color-text-disabled` e abas presas ao topo, com o traço de 2px na ativa.
- I. Origem do conceito, organização empilhada, num diálogo de 760px. O cabeçalho tem o
  nome, o `GeneratedByLLM` de 24px só se o conceito foi gerado e não renomeado, e a linha de fatos
  "aparece em N de M problemas". Na fileira de problemas, o rótulo "Problema" com `file-code`
  aparece uma vez, e cada aba leva só o identificador, com qualquer número de problemas. Cada aba
  tem, nesta ordem, três blocos.
  - "Enunciado do problema N", o texto do pacote, sem estrelas. Sem enunciado, uma frase em cinza.
  - "Justificativa do modelo de linguagem", com as estrelas antes do rótulo e a dica ?, uma ou
    duas frases traduzidas dos KCs candidatos do par. Sem candidato, que é o vínculo feito pelo
    professor, a frase "O professor ligou este conceito a este problema. Não há justificativa nem
    trecho do modelo."
  - "Soluções que o modelo leu", com a dica ? e o bloco de código com as abas "Solução 1" a
    "Solução 5" (`file-check`), numeradas pela posição no prompt. Abre na solução do trecho, com as
    linhas destacadas em `--color-model-soft`, o número delas em `--color-model-strong` e estrelas
    pequenas na aba, e o bloco rola por dentro até a primeira linha destacada, como a maquete
    aprovada (`base.js:515-522`). O trecho descartado mostra "O modelo apontou um trecho que não
    está nas soluções, e o app o descartou." e abre na Solução 1. Sem a tentativa do aluno. O código
    mantém o `\r\n` e as tabulações (tab-size 4), e as linhas longas rolam dentro do bloco. A dica
    das soluções evita a palavra justificativa.
  - O rótulo "Justificativa do modelo de linguagem" já separa na tela a `translated_reasoning` do
    trecho. Os documentos que chamam o trecho de justificativa (`GLOSSARY.md:152`,
    `DECISIONS.md:249-250`, `DEVELOPMENT.md:1016-1017`) ficam como estão.
  - Uma rota nova, uma chamada por conceito, devolve por problema ligado o identificador, o
    enunciado ou nulo, as justificativas traduzidas, o trecho (posição, primeira e última linha) ou
    nulo e as soluções, até cinco (posição e código). O trecho fica depois de desligar e religar,
    e o vínculo do professor se reconhece pela falta de candidato.
- J. Problema sem conceito bloqueia o Aprovar, na tela e no `ApproveKnowledgeComponentsUseCase`. A
  rota da tela entrega a contagem de execuções corretas por problema, e o balão do número em
  vermelho traz o motivo. Com a contagem 0, o motivo é "Ninguém acertou este problema ainda. O
  modelo de linguagem precisa de execuções corretas para extrair conceitos. Ligue um conceito
  clicando nas células." Nos outros casos, que hoje não acontecem, é "Este problema está sem
  conceito. Ligue um conceito clicando nas células." Abaixo do motivo vem o enunciado, porque o
  balão do número é o mesmo de O, e o professor precisa dele justamente para escolher o conceito.
  A maquete faz assim, com o título "Problema N sem conceito" (`screen.js:255-264`). O Aprovar
  fica só desabilitado, com o `disabled` nativo de hoje e sem balão. O problema sem conceito
  continua visível pelo número e pela contagem em vermelho na matriz e pela linha de fatos.
- K. Marcador de gerado pelo `kc.updated_at`, numa migração nova. A coluna segue o padrão
  `updated_at`, e outra entidade que precisar dele ganha o mesmo nome. Renomear grava a data junto
  do nome, e renomear para o mesmo nome não grava nada. O soft delete continua gravando só o
  `deleted_at`, e ligar e desligar mexem na `problem_kc`, não no `kc`. O marcador aparece com
  `generated_name` preenchido e `updated_at` vazio, porque hoje o renomear é a única edição do
  `kc`, e uma edição nova do `kc` que não seja do nome precisa rever o marcador. O conceito criado
  pelo professor não tem `generated_name`. As turmas antigas, cujas extrações não têm
  `generated_name`, são apagadas pelo Leo, que faz uma nova extração pela aplicação.
- L. Novo conceito. Diálogo com o nome e caixas de marcar com o número, o começo do
  enunciado e a contagem de conceitos de cada problema. "Criar" fica desabilitado até ter nome e um
  problema, e o nome repetido é recusado como hoje. O backend passa a recusar `problem_ids` vazio
  com o 422 da validação do DTO (`Field(min_length=1)`), como o nome em branco da turma
  (`edit_classrooms_dto.py:9-12`), porque é a forma do pedido e a tela nunca manda a lista vazia. O
  422 fica só como defesa da api, porque o `detail` dele é uma lista, que o `readDetail()` lê como
  texto vazio (`client.ts:42-49`).
- M. Conceitos aprovados, revisto pelo Leo. A matriz continua editável, e o Aprovar continua à
  vista, apagado e sem clique. A primeira edição depois da aprovação (ligar, desligar, renomear,
  remover ou criar) mostra um aviso como "Editar a matriz agora reabre todos os conceitos para
  aprovação", com Cancelar e a ação de seguir. Quando a edição já tem confirmação própria, que é
  remover e tirar o último problema do conceito, o aviso entra como uma linha nela, para não abrir
  dois diálogos seguidos. Renomear e Novo conceito são formulários, e neles o aviso é a mesma
  linha, dentro do formulário e acima dos botões, também para não abrir dois diálogos seguidos. O
  diálogo de aviso abre só no clique direto na célula. Depois da edição o exercício volta a
  rascunho, e o Aprovar volta a habilitar.
- N. Matriz com 25 conceitos. A coluna do nome ocupa a sobra do cartão e corta com
  reticências, com o nome inteiro no balão logo abaixo, que é o comportamento do `Tooltip` de hoje.
  A primeira coluna fica presa na rolagem lateral. A ordem é calculada só ao abrir a tela, por
  recorrência decrescente, com empate pelo nome em pt-BR e depois pelo id, e fica fixa enquanto o
  professor edita, porque a linha que pula de lugar debaixo do mouse desorienta. Nas recargas, os
  conceitos que já estavam mantêm a posição, o conceito novo entra no fim e o removido sai. Ao
  sair e voltar à tela, a ordem é recalculada. Sem ordenação clicável. A linha mede uns 41px por
  causa dos botões de ícone, e o Leo aceitou.
- O. Enunciado. A aba Problemas tem Problema, Enunciado e Conceitos. O enunciado não leva
  estrelas e quebra linha, e sem ele a célula diz "sem enunciado" em cinza. O balão do número do
  problema na matriz traz o enunciado, com até uns 360px. A `description` sai dos dois DTOs, da
  entidade `Problem`, do `SqliteProblemRepository`, do `schema.d.ts` e do banco
  (`ALTER TABLE problem DROP COLUMN description`), o que apaga 20 textos do método antigo, 10 da
  turma 3, já removida, e 10 da turma 5. A rota `GET /assignments/{id}/problems` fica só com o
  `problem_id`, e o front não a usa.
- P. O nome gerado em inglês não aparece em lugar nenhum.
- Q. `math.abs` e "Operadores lógicos (e, ou)" ficam como estão, fiéis ao Duan e à tradução, porque
  mudar o prompt da tradução invalida o cache da regressão do A439.
- R. O 409 de modelo antigo, que a Análise ignora, fica para a tela Análise.
- S. A rota `GET /assignments/{id}/problems/knowledge-components` passa a devolver, por problema, o
  enunciado e a contagem de execuções corretas, por conceito, o marcador, e no exercício a data da
  extração, que é o `updated_at` do `kc_job` concluído mais recente. A data aparece no fuso do
  navegador, e 2h30 UTC de 07/10 vira 06/10/2026 em Brasília.
- T. Número do problema. As linhas da aba Problemas e a lista do Novo conceito mostram só o
  número, pela mesma regra das abas da origem, porque o cabeçalho já diz Problema. A aba Problemas
  da Análise muda quando ela for refeita.
- U. Peças da maquete que as outras decisões não citam. Entram o rodapé do cartão, com a frase de
  apoio no rascunho, a de consulta no treinado e nada com os conceitos aprovados, e as notas sobre
  as estrelas nos diálogos de renomear e do Novo conceito, com os textos da maquete. Ficam de fora
  o rótulo "Origem do conceito" acima do título, os fatos "criado pelo professor" e "renomeado pelo
  professor", a legenda acima do bloco e o balão na aba da solução.
- V. A página de referência passa à v6 com `git mv`, pela regra do `DESIGN.md:469`, porque esta
  rodada traz desenho novo e tem maquete, e não a revisão no lugar como a de 08/10.
- W. A api é recriada depois da etapa 6, antes do front, pela sequência da seção "Depois
  do plano, com o Leo". Contra a api antiga a Conceitos perde os campos novos, e só a api recriada
  volta a servir o `npm run types`.
- X. Nenhum código trata as extrações antigas. Nos exercícios 1 e 7 do `app.db` (o A439 da turma 1
  e o exercício da turma 5), sem solução amostrada, candidato nem trecho, a lupa abre normalmente e
  mostra o que houver, e todo vínculo parece do professor. É desenvolvimento, e essas turmas serão
  apagadas. O problema sem solução amostrada, que é um caso real de uma extração nova, mostra em
  cinza "Ninguém acertou este problema, então o modelo não leu nenhuma solução dele." no lugar do
  bloco de código, quando a lista de soluções vem vazia. Nas extrações antigas a lista vem vazia em
  todo problema, então a frase aparece também nos problemas com acertos. O Leo aceita esse dado
  errado de propósito, porque essas turmas serão apagadas.

## Padrões adotados

- Cada etapa deixa o app funcionando. As etapas do backend acrescentam ao contrato, ou tiram na
  mesma etapa o que a tela deixa de usar (o mesclar e a descrição). As duas recusas novas da etapa
  4 só pegam o que a tela de hoje já evita ou mostra pelo `editErrorText`
  (`knowledgeComponents.ts:57-62`), então o front compila e funciona em todo commit.
- Duas migrações, `0021_kc_updated_at.sql` na etapa 4 e `0022_drop_problem_description.sql` na
  5b. O runner aplica cada arquivo numa transação junto com o `user_version` (`runner.py:36-48`) e
  divide os comandos por `;` depois de tirar os comentários `--` (`runner.py:16-33`), então nenhum
  `;` vai dentro de texto, e o comentário `--` segue a regra (`code_comments_test.py:20`). O
  `DROP COLUMN` tem precedente em `0009_glossary_names_and_progsnap_id.sql:22-23` e foi testado num
  banco temporário fora do repositório, com o SQLite 3.50.0 da imagem e `foreign_keys=ON`. São
  quatro as tabelas que apontam para `problem`, a `submission` (`0011_problem_table.sql:28`), a
  `problem_kc`, a `sampled_solution` (`0018_sampled_solution.sql:8`) e a `candidate_kc`
  (`0019_candidate_kc_and_kc_job_model.sql:12`), e a `kc_evidence` aponta para a
  `sampled_solution`. O `foreign_key_check` voltou vazio.
- A regra do marcador mora na entidade. `KnowledgeComponent` ganha `updated_at` e a propriedade
  `is_generated_by_llm` (`generated_name` preenchido e `updated_at` vazio), e o DTO só copia. O
  campo entra no próprio `KnowledgeComponentDTO` (`edit_knowledge_components_dto.py:39-41`), porque
  o mesmo conceito sai em três respostas, a de criar (`add_knowledge_component_use_case.py:57`), a
  de renomear (`rename_knowledge_component_use_case.py:42`) e a da rota da tela
  (`list_problem_knowledge_components_use_case.py:53`), e um DTO só evita que elas discordem.
- Renomear para o mesmo nome devolve o conceito sem gravar, sem `updated_at` e sem voltar o
  aprovado a rascunho, o que hoje acontece (`rename_knowledge_component_use_case.py:41`). A recusa
  do exercício treinado (`:39`) vem antes da saída, e o 409 continua.
- A contagem de execuções corretas e o código das soluções vêm do `ISubmissionRepository`, porque
  `classroom_import` é a dona da tabela `submission`, e `knowledge_components` já importa essa
  interface (`run_kc_generation_use_case.py:7`). Os dois métodos novos,
  `count_correct_runs_by_problem()` e `get_codes()`, usam SQL direto, sem DataFrame. A contagem usa
  o mesmo filtro do `list_correct_runs()` (`sqlite_submission_repository.py:79-84`) e acrescenta
  `AND problem_id IS NOT NULL`, porque a coluna aceita nulo (`0011_problem_table.sql:20`) e o
  `GROUP BY` devolveria uma chave nula, que o `int()` do dicionário não converte. O gerador já
  descarta o nulo do mesmo jeito (`kcgen_kt_generator.py:93`). Um problema sem acerto não volta no
  `GROUP BY`, e o caso de uso completa com 0. O `get_codes()` filtra só pelo id, porque a solução
  amostrada já aponta uma execução correta.
- A data da extração vem de `find_latest_done()`, um método novo do repositório do job, que hoje
  não lê por exercício (`kc_generation_job_repository.py:12-26`). O `updated_at` do job concluído é
  gravado pelo `mark_done()` (`sqlite_kc_generation_job_repository.py:73-76`).
- A regra do Aprovar é uma `IBusinessRule` em `domain/rules`, a
  `EveryProblemHasAKnowledgeComponentRule`, com a lista dos problemas no texto, no formato de
  `problems_belong_to_assignment_rule.py:16-18`. Ela fica calada quando o exercício não existe, que
  é o 404, e quando ele não tem nenhum conceito. O `AssignmentHasKnowledgeComponentsRule` fica,
  porque é ele que recusa o rascunho sem conceito, e o `WriteUseCase` junta as recusas de todas as
  regras (`write_use_case.py:16`). Sem o silêncio, o rascunho com problemas e nenhum conceito
  receberia as duas mensagens, uma delas com a lista inteira dos problemas.
- A rota da origem mora em `knowledge_components`, a dona das chaves estrangeiras de
  `sampled_solution`, `candidate_kc` e `kc_evidence` (migrações `0018` a `0020`), e lê o problema e
  a execução pelas interfaces do `domain/` das outras funcionalidades, como a regra de dependência
  permite. O caso de uso é uma leitura simples, com `execute(kc_id)` e o 404 do
  `get_active_knowledge_component()` (`active_knowledge_component.py:13-22`). Ele filtra em memória
  os `list_by_assignment()` que já existem, porque o A439 tem 93 candidatos, 83 trechos e 50
  soluções. O vínculo do professor é o par sem candidato, e o trecho descartado é o par com
  candidato e sem trecho. `candidate_kc` e `kc_evidence` não têm soft delete
  (`ARCHITECTURE.md:138`), então desligar e religar mantém o trecho.
- A justificativa traduzida é anulável (`candidate_knowledge_component_entity.py:16`,
  `0019_candidate_kc_and_kc_job_model.sql:9`), e a nula sai da lista, para a resposta não quebrar
  no Pydantic. O gerador sempre a preenche (`kcgen_kt_generator.py:169-175`), então o caso só
  aparece numa linha gravada fora da extração.
- A regra do vínculo do professor só vale para a extração que grava as soluções, os candidatos e
  os trechos (migrações `0018` a `0020`). No `app.db` de 08/10/2026, os exercícios 1 (A439 da turma
  1, o treinado) e 7 (turma 5) têm 15 conceitos cada, de extrações de 21/06 e 25/09, sem nenhuma
  linha em `sampled_solution`, `candidate_kc` e `kc_evidence` e sem `generated_name`. Neles, todo
  par parece do professor, o que é falso, e nenhum código trata esse caso (X).
- Um problema sem execução correta não tem solução amostrada, e numa extração nova ele só tem
  conceito pelo vínculo do professor. A lista de soluções vem vazia, e o bloco "Soluções que o
  modelo leu" mostra em cinza a frase de X no lugar do `CodeBlock`, que não é desenhado sem
  solução.
- Os testes do backend seguem o padrão de hoje. Controller pela fixture `api_client`, regra com
  fakes em memória e `SimpleNamespace` (`knowledge_component_rules_test.py`), repositório com
  `tmp_db` e migração com `_migrations_up_to()` (`migrations_test.py:272`). A extração semeada para
  os testes da rota da tela e da origem sai de uma função nova em
  `tests/fixtures/knowledge_components.py`, como pede o `ARCHITECTURE.md`.
- `GeneratedByLLM` e a linha de fatos (`FactsLine`) moram em `components/`, como o `GeneratedByML` e
  o `PageHeader`, porque são peças de produto. O `CodeBlock` e as variantes novas de `Dialog`,
  `Tabs`, `Tooltip` e `DataTable` moram em `components/ui/`, sem domínio, com a política
  vinda por props. O `CodeBlock` recebe as estrelas da aba como `ReactNode`, para `ui/` não importar
  o `GeneratedByLLM`. A matriz, a aba Problemas, a origem, o Novo conceito e o aviso de reabrir
  moram em `features/knowledge_components/components/`, os hooks em `api/knowledgeComponents.ts` e
  as funções puras em `knowledgeComponents.ts`, porque o react-refresh cobra que um `.tsx` exporte
  só componentes. As fronteiras são conferidas pelo `src/web/architecture.test.ts`.
- O `KnowledgeComponentEditor` fica e vira o dono do cartão, das mutações, de um estado único dos
  diálogos (fechado, novo, origem, renomear, remover, desligar e reabrir) e da ordem fixa da matriz,
  sempre com ids.
- Cada variante tem a sua situação de uso. O `Dialog` ganha `size` (440px e o largo de 760px), o
  `Tooltip` ganha `size` (260px e o largo de 360px, com a meia largura do limite lateral
  acompanhando, hoje fixa em 130 em `Tooltip.tsx:24`), o `GeneratedByLLM` tem uma variante por lugar
  (20px no fim do texto, 24px no título, 18px antes do rótulo e 16px na aba da solução), a
  `DataTable` ganha o layout fixo, a primeira coluna presa, as células que quebram linha e alinham
  à esquerda e o rótulo que ocupa a célula, e as `Tabs` ganham as ações à direita, o rótulo à
  esquerda e o `ariaLabel` da aba. O `Button` não muda.
- O balão ganha um título opcional, em 600 numa linha própria, e o texto passa a
  `white-space: pre-line`, como na maquete (`base.css:1524`, `:1529-1533`). Hoje ele só recebe
  `text: string` e usa `white-space: normal` (`Tooltip.tsx:14`, `Tooltip.css:16`). O balão do número
  do problema leva o título "Problema N", ou "Problema N sem conceito", e separa o motivo do
  enunciado por uma linha em branco. Nenhum texto de balão de hoje tem quebra de linha, então os
  outros balões não mudam.
- O `Dialog` ganha, em todos os tamanhos, a altura máxima de `calc(100vh - 48px)`, com o cabeçalho
  e o rodapé presos e o corpo rolando por dentro, como na maquete (`base.css:1551-1572`). Os
  diálogos de hoje cabem na janela e não mudam, o que a linha de base das outras telas confere.
- Balão dentro de diálogo. O `Tooltip` faz o portal em `document.body` (`Tooltip.tsx:52-58`), e o
  `<dialog>` modal fica acima de tudo, então o balão nasce por baixo dele. O portal passa ao
  `dialog[open]` mais próximo do elemento, e ao `body` fora de diálogo. O conserto também vale para
  o diálogo do aluno da Análise, que a linha de base confere antes.
- O marcador do título da origem fica fora do `h2`, para o nome acessível do diálogo continuar só o
  nome do conceito (`Dialog.tsx:43`, `:59-61`).
- A vírgula da linha de fatos vai como texto no DOM, e não como pseudo-elemento, porque o jsdom e o
  leitor de tela não leem pseudo-elemento.
- O bloco de código tem a altura máxima num valor fixo do CSS, porque o `tokens.test.ts` recusa
  variável que não está no `tokens.css` (`tokens.test.ts:41-48`). Os tokens que a tela usa já
  existem, e nenhum token novo entra.
- A ordem da matriz é calculada na primeira carga dos dados do exercício e fica fixa nas recargas
  (N). Uma função pura em `knowledgeComponents.ts`,
  `stableKnowledgeComponentOrder(previousIds, knowledgeComponents)`, devolve a ordem nova a partir
  da anterior, e o `KnowledgeComponentEditor` guarda só a lista de ids. Ele continua montado nas
  recargas e na troca de abas, porque o `QueryStates` mantém o conteúdo enquanto há dado
  (`states.tsx:79-85`), e desmonta ao sair da tela, o que recalcula a ordem. A lista é estado
  porque depende das cargas anteriores e não se calcula da resposta atual, e o editor a ajusta na
  própria renderização quando os conceitos mudam, sem `useEffect`, que no projeto só sincroniza
  com algo de fora do React (`ARCHITECTURE.md:274-278`).
- O nome do conceito na matriz mostra o balão sempre, como o rótulo da `DataTable`
  (`DataTable.tsx:26-32`), mas sem o teto de 150px do `.data-table__label` (`DataTable.css:65-71`),
  porque a coluna do nome ocupa a sobra do cartão (N). A célula do nome é um flex com
  `min-width: 0`, o nome corta com reticências e o `GeneratedByLLM` fica depois dele, sempre à
  vista, como a `.scr-name` da maquete (`screen.css:80-92`).
- O fio da coluna presa só aparece quando há algo rolado por baixo dela, como na maquete
  (`screen.css:63-73`, `screen.js:144`). A `DataTable` com a primeira coluna presa liga a classe
  `is-scrolled` no `onScroll` do invólucro, quando o `scrollLeft` passa de 0. Assim a regra "Sem fio
  vertical" (`DESIGN.md:297-299`) só cede quando a coluna cobre outra, e o `DESIGN.md` registra isso
  na etapa 0.
- O erro de ligar, desligar e aprovar aparece numa `OutcomeMessage` dentro do cartão, como o erro de
  hoje (`KnowledgeComponentEditor.tsx:82-86`).
- As datas dos testes do front ficam ao meio-dia UTC, porque o container roda em UTC
  (`lib/format.test.ts:30-31`).
- O `schema.d.ts` é regerado sem subir a api, em toda etapa do backend que muda o contrato (3, 4,
  5a, 5b e 6), e nunca editado à mão. O `npm run types` lê `http://api:8099/openapi.json`
  (`src/web/package.json`), e a api só serve o contrato novo depois de recriada, o que aplica as
  migrações ao `app.db` (`src/api/main.py:31-41`). O `create_app().openapi()` não roda o lifespan e
  não abre banco nenhum, e o arquivo gerado assim no `1446a21` saiu igual, byte a byte, ao
  versionado. Os comandos estão em Verificação.

## Mudanças por camada

O mesmo trabalho das etapas, visto por camada, com o arquivo de cada peça e a etapa em que ela
entra. O detalhe de cada mudança fica na etapa.

### Backend

Os arquivos ficam em `src/api/knowledge_components/`, salvo onde a linha diz outra funcionalidade.

**Entidades**, em `domain/entities/`.

| Entidade | Arquivo | Mudança | Etapa |
|---|---|---|---|
| `KnowledgeComponent` | `knowledge_component_entity.py` | Ganha `updated_at`, anulável, e a propriedade `is_generated_by_llm` | 4 |
| `Problem` (`assignments/problems`) | `problem_entity.py` | Perde a `description` | 5b |

As outras ficam. A origem lê a `SampledSolution`, o `CandidateKnowledgeComponent` e a
`KnowledgeComponentEvidence` como estão, com a `translated_reasoning`
(`candidate_knowledge_component_entity.py:16`) e as linhas inicial e final do trecho
(`knowledge_component_evidence_entity.py:13-15`) que já existem. O `ProblemKnowledgeComponent` não
muda, porque ligar e desligar só criam e removem vínculos. O `KnowledgeComponentGenerationJob` já
tem o `updated_at` que a data da extração lê (`kc_generation_job_entity.py:18`).

**Value objects.** Nenhum novo. Um value object no projeto é um valor com regra ou cálculo
próprio, como o `ProgSnapAssignmentId`, que recusa o que não é int
(`progsnap_assignment_id.py:14-17`), o `JobStatus`, que fecha os estados de um job
(`job_status.py:8-12`), e as estatísticas de `submission_statistics.py`, contadas do dado limpo. O
que esta tela acrescenta é atributo (`updated_at`), propriedade derivada (`is_generated_by_llm`) ou
formato de leitura (os DTOs da origem), e as linhas inicial e final do trecho já vivem na
entidade `KnowledgeComponentEvidence`.

**Repositórios.** A interface mora em `domain/interfaces/` e a implementação em
`infrastructure/repositories/`, com o mesmo nome de arquivo e o prefixo `sqlite_`.

| Interface | Arquivo | Mudança | Etapa |
|---|---|---|---|
| `IKnowledgeComponentRepository` | `knowledge_component_repository.py` | `rename(kc_id, name, updated_at)`, e o `get` e o `list_by_assignment` leem a coluna | 4 |
| `IProblemKnowledgeComponentRepository` | `problem_knowledge_component_repository.py` | Sai o `move_bindings` | 3 |
| `IProblemRepository` (`assignments/problems`) | `problem_repository.py` | Nenhum método novo, e o SQL deixa a `description` | 5b |
| `ISubmissionRepository` (`classroom_import`) | `submission_repository.py` | Ganha `count_correct_runs_by_problem()` na 5a e `get_codes()` na 6 | 5a, 6 |
| `IKnowledgeComponentGenerationJobRepository` | `kc_generation_job_repository.py` | Ganha `find_latest_done()` | 5a |
| `ISampledSolutionRepository` | `sampled_solution_repository.py` | Sem mudança, e o `list_by_assignment` passa a servir a origem | 6 |
| `ICandidateKnowledgeComponentRepository` | `candidate_knowledge_component_repository.py` | Sem mudança, e o `list_by_assignment` passa a servir a origem | 6 |
| `IKnowledgeComponentEvidenceRepository` | `knowledge_component_evidence_repository.py` | Sem mudança, e o `list_by_assignment` passa a servir a origem | 6 |

Os dois métodos novos da execução moram no `ISubmissionRepository`, e não em
`knowledge_components`, porque `classroom_import` é a dona da tabela `submission`, e
`knowledge_components` já importa essa interface (`run_kc_generation_use_case.py:7`). Hoje o
`list_by_assignment` das soluções, dos candidatos e dos trechos só é chamado nos testes.

**DTOs**, em `application/dtos/`.

| DTO | Arquivo | Mudança | Etapa |
|---|---|---|---|
| `KnowledgeComponentDTO` | `edit_knowledge_components_dto.py` | Ganha `is_generated_by_llm` | 4 |
| `AddKnowledgeComponentDTO` | `edit_knowledge_components_dto.py` | `problem_ids` obrigatório e não vazio, pelo `Field(min_length=1)` | 4 |
| `MergeKnowledgeComponentsDTO`, `MergedKnowledgeComponentsDTO` | `edit_knowledge_components_dto.py` | Saem | 3 |
| `ProblemKnowledgeComponentsDTO` | `list_problem_knowledge_components_dto.py` | Ganha `statement` e `correct_run_count` na 5a e perde a `description` na 5b | 5a, 5b |
| `ListProblemKnowledgeComponentsResponseDTO` | `list_problem_knowledge_components_dto.py` | Ganha `extracted_at`, nulo sem job concluído | 5a |
| `ProblemDTO` (`assignments/problems`) | `list_problems_dto.py` | Fica só com o `problem_id` | 5b |
| `KnowledgeComponentOriginDTO` | `get_knowledge_component_origin_dto.py`, novo | `kc_id`, `name`, `is_generated_by_llm` e os problemas | 6 |
| `ProblemOriginDTO` | `get_knowledge_component_origin_dto.py`, novo | `problem_id`, `statement`, as justificativas traduzidas, o trecho ou nulo e as soluções | 6 |
| `KnowledgeComponentEvidenceDTO` | `get_knowledge_component_origin_dto.py`, novo | O trecho, com `position`, `first_line` e `last_line` | 6 |
| `SampledSolutionDTO` | `get_knowledge_component_origin_dto.py`, novo | A solução, com `position` e `code` | 6 |

Os DTOs da origem não levam o `generated_name` nem a justificativa em inglês (P), nem um campo para
as extrações antigas (X).

**Casos de uso**, em `application/use_cases/`.

| Caso de uso | Arquivo | Mudança | Etapa |
|---|---|---|---|
| `GetKnowledgeComponentOriginUseCase` | `get_knowledge_component_origin_use_case.py`, novo | Leitura com `execute(kc_id)`, que junta por problema ligado o enunciado, os candidatos, o trecho e as soluções | 6 |
| `RenameKnowledgeComponentUseCase` | `rename_knowledge_component_use_case.py` | Sai sem gravar no mesmo nome e grava `updated_at = utc_now_iso()` nos outros casos | 4 |
| `ApproveKnowledgeComponentsUseCase` | `approve_knowledge_components_use_case.py` | Ganha o `IProblemRepository`, o `IProblemKnowledgeComponentRepository` e a regra nova | 4 |
| `ListProblemKnowledgeComponentsUseCase` | `list_problem_knowledge_components_use_case.py` | Lê o marcador na 4, ganha o `ISubmissionRepository` e o repositório do job na 5a e deixa a `description` na 5b | 4, 5a, 5b |
| `ListProblemsUseCase` (`assignments/problems`) | `list_problems_use_case.py` | Deixa a `description` | 5b |
| `AddKnowledgeComponentUseCase` | `add_knowledge_component_use_case.py` | Só a montagem do `KnowledgeComponentDTO`, com o marcador | 4 |
| `MergeKnowledgeComponentsUseCase` | `merge_knowledge_components_use_case.py` | Sai | 3 |

**Regras**, em `domain/rules/`.

| Regra | Arquivo | Mudança | Etapa |
|---|---|---|---|
| `EveryProblemHasAKnowledgeComponentRule` | `every_problem_has_a_knowledge_component_rule.py`, nova | Recusa o Aprovar com problema sem conceito, calada sem exercício e sem conceito | 4 |
| `KnowledgeComponentsAreDistinctRule` | `knowledge_components_are_distinct_rule.py` | Sai com o mesclar | 3 |
| `KnowledgeComponentsBelongToAssignmentRule` | `knowledge_components_belong_to_assignment_rule.py` | Sai com o mesclar | 3 |

**Rotas**, em `presentation/controllers/`.

| Rota | Arquivo | Mudança | Etapa |
|---|---|---|---|
| `GET /knowledge-components/{kc_id}/origin` | `knowledge_components_controller.py` | Nova | 6 |
| `POST /knowledge-components/merge` | `knowledge_components_controller.py` | Sai | 3 |
| `GET /assignments/{id}/problems/knowledge-components` | `problems_controller.py` (`assignments/problems`) | A resposta ganha o marcador na 4, o enunciado, a contagem e a data na 5a e perde a `description` na 5b | 4, 5a, 5b |
| `GET /assignments/{id}/problems` | `problems_controller.py` (`assignments/problems`) | A resposta fica só com o `problem_id` | 5b |
| `PUT /knowledge-components/{kc_id}` | `knowledge_components_controller.py` | A resposta ganha o marcador, e o mesmo nome responde 200 sem gravar | 4 |
| `POST /knowledge-components` | `knowledge_components_controller.py` | A validação recusa `problem_ids` vazio ou ausente com 422 | 4 |

As fábricas acompanham. A do mesclar sai do `dependencies.py` na 3, a do aprovar monta dois
repositórios a mais na 4 (`dependencies.py:181-188`), a da rota da tela monta mais dois na 5a
(`assignments/problems/presentation/dependencies.py:36-44`) e a da origem nasce na 6.

**Migrações**, em `src/api/shared/infrastructure/database/migrations/`.

| Migração | Comando | Etapa |
|---|---|---|
| `0021_kc_updated_at.sql` | `ALTER TABLE kc ADD COLUMN updated_at TEXT` | 4 |
| `0022_drop_problem_description.sql` | `ALTER TABLE problem DROP COLUMN description` | 5b |

### Front

Os arquivos ficam em `src/web/src/`.

**Componentes de produto**, em `components/`.

| Componente | Arquivo | Mudança | Etapa |
|---|---|---|---|
| `FactsLine` | `FactsLine.tsx`, novo | A linha de fatos, com a vírgula como texto e o item de alerta | 7 |
| `PageHeader` | `PageHeader.tsx` | Ganha o encaixe `facts`, e a `description` fica | 7 |
| `GeneratedByLLM` | `GeneratedByLLM.tsx`, novo | As estrelas, com as quatro variantes de tamanho | 8 |

**Primitivas**, em `components/ui/`.

| Primitiva | Arquivo | Mudança | Etapa |
|---|---|---|---|
| `Tabs` | `Tabs.tsx` | O invólucro com as ações à direita, o rótulo à esquerda e o `ariaLabel` da aba | 8 |
| `Tooltip` | `Tooltip.tsx` | O `size` largo, o título, o `white-space: pre-line` e o portal no diálogo aberto | 8 |
| `DataTable` | `DataTable.tsx` | O layout fixo, a primeira coluna presa, as células que quebram linha e o rótulo sem teto | 8 |
| `Dialog` | `Dialog.tsx` | O `size` largo, os encaixes do título e da linha de fatos e a altura máxima | 11 |
| `CodeBlock` | `CodeBlock.tsx`, novo | O bloco de código com abas, o destaque e a rolagem até o trecho | 11 |
| `Button` | `Button.tsx` | Não muda, e o Aprovar desabilitado usa o `disabled` nativo (J) | Nenhuma |

**Componentes da funcionalidade**, em `features/knowledge_components/components/`.

| Componente | Mudança | Etapa |
|---|---|---|
| `KnowledgeComponentMatrix.tsx` | Novo, a matriz | 9a |
| `NewKnowledgeComponentDialog.tsx` | Novo na 9b, no lugar do `AddKnowledgeComponentDialog`, e a linha do aviso de reabrir na 10 | 9b, 10 |
| `ProblemStatementsTable.tsx` | Novo, a aba Problemas | 9c |
| `ReopenApprovalDialog.tsx` | Novo, o aviso de reabrir | 10 |
| `KnowledgeComponentOriginDialog.tsx` | Novo, a origem do conceito | 11 |
| `KnowledgeComponentEditor.tsx` | Vira o dono do cartão com as abas, das mutações, dos diálogos e da ordem fixa | 9a a 11 |
| `AssignmentWorkspace.tsx` | Recebe o `PageHeader` com a linha de fatos na 7 e o pronto para conceitos com os blocos na 9c | 7, 9c |
| `KnowledgeComponentsPage.tsx` (em `pages/`) | O `PageHeader` desce para o `AssignmentWorkspace`, e saem o título fixo e o `DESCRIPTION` | 7 |
| `RenameKnowledgeComponentDialog.tsx` | A nota das estrelas na 9b e a linha do aviso de reabrir na 10 | 9b, 10 |
| `RemoveKnowledgeComponentDialog.tsx` | A linha do aviso de reabrir | 10 |
| `UnlinkKnowledgeComponentDialog.tsx` | O `UnlinkTarget` só com o id e o nome na 9a e a linha do aviso de reabrir na 10 | 9a, 10 |
| `MergeKnowledgeComponentsDialog.tsx` | Sai | 3 |
| `KnowledgeComponentsCard.tsx`, `ApprovalBar.tsx` | Saem | 9a |
| `AddKnowledgeComponentDialog.tsx` | Sai | 9b |
| `ProblemsCard.tsx` | Sai, com o `ProblemsCard.css` | 9c |

**Hooks**, em `features/knowledge_components/api/knowledgeComponents.ts`.

| Hook | Mudança | Etapa |
|---|---|---|
| `useMergeKnowledgeComponents` | Sai | 3 |
| `useCreateKnowledgeComponent` | Passa a receber o nome e os problemas | 9b |
| `useKnowledgeComponentOrigin(kcId)` | Novo, com a chave própria em `knowledgeComponentKeys` | 11 |
| `useRefreshAssignment` | Também invalida a origem | 11 |

**Funções puras**, em `features/knowledge_components/knowledgeComponents.ts`.

| Função | Mudança | Etapa |
|---|---|---|
| `mergedProblemIds()` | Sai | 3 |
| Contagens da linha de fatos | Novas, com a lista dos problemas sem conceito | 7 |
| `knowledgeComponentsOf()` | Ordena por recorrência decrescente, nome em pt-BR e id, a ordem da primeira carga | 9a |
| `stableKnowledgeComponentOrder()` | Nova, a ordem fixa (N) | 9a |
| Desfecho do clique na célula | Nova, entre recusar, confirmar e desligar direto | 9a |
| Nome normalizado | Nova, para recusar o nome repetido | 9b |
| Texto do aviso de reabrir | Constante nova | 10 |
| Classificação do painel da origem | Nova, entre com trecho, trecho descartado e vínculo do professor | 11 |

Nenhuma função calcula um motivo para o Aprovar desabilitado (J).

**Tipos.** O `http/schema.d.ts` é regerado do OpenAPI nas etapas 3, 4, 5a, 5b e 6, e nunca
editado à mão.

## Etapas

Cada etapa é um commit, com uma revisão independente do diff contra o plano antes de commitar. O
teste vem antes do código em cada mudança de comportamento. Em toda etapa, o comentário que a etapa
torna falso é corrigido em qualquer arquivo de `src/` e `tests/`, pela busca dos termos que ela muda
(descrição, description, mesclar, merge, ApprovalBar, PATCH).

### 0. Registro e nomes, antes do código

- Este plano vira `docs/CONCEPTS_SCREEN_PLAN.md`, com a tabela de Estado. O plano não cita o
  arquivo de decisões nem os insumos do scratchpad como caminho permanente. O item 4 da seção 9 do
  `IMPLEMENTATION_PLAN.md` (`:278-280`) e a linha "9 e 11 a 17" do Estado do KCGen-KT no
  `DEVELOPMENT.md` (`:1049`) apontam para ele.
- `IMPLEMENTATION_PLAN.md`. O B1 (`:92-93`), o B2 (`:95-99`) e a parte da Conceitos do B8
  (`:127-130`) apontam para este plano. Na seção 6, a pendência do desenho da Conceitos
  (`:193-198`) aponta para o plano, e a do import-linter quebrado (`:199-203`) sai, porque o
  `002c2ef` corrigiu o teste e o `1ea6299` pôs o linter na suíte. Entram o 409 de modelo antigo para
  a tela Análise (R, `AnalysisCard.tsx:39`, `:60`, `:74`) e a ressalva das turmas antigas (K e X). A
  seção 9 (`:255-257`) registra que o Leo decidiu apagar a turma CSEDM Spring 2019 e a turma 5.
- `GLOSSARY.md`. Entram no backend o `updated_at` do `kc`, `is_generated_by_llm`,
  `correct_run_count`, `count_correct_runs_by_problem()`, `get_codes()`, `extracted_at`,
  `find_latest_done()` e a rota `GET /knowledge-components/{kc_id}/origin`. O `updated_at` já
  existe no `training_job` e no `kc_job` (`0003_training_job_progress.sql:6`,
  `0005_kc_index_and_kc_job.sql:12`), no `kc_job` como batimento do progresso e no `training_job`
  só com a hora do fim (`sqlite_training_job_repository.py:49-54`), e o glossário diz o sentido de
  cada um. O glossário não tem linha de caso de uso, de DTO nem de regra concreta
  (nenhum `UseCase` nem `DTO` em `GLOSSARY.md`), e esses nomes juntam um termo dele ao sufixo do
  papel (`ARCHITECTURE.md:148`).
  São a `EveryProblemHasAKnowledgeComponentRule`, o `GetKnowledgeComponentOriginUseCase`, o
  `KnowledgeComponentOriginDTO`, o `ProblemOriginDTO`, o `KnowledgeComponentEvidenceDTO` (o trecho,
  com `position`, `first_line` e `last_line`) e o `SampledSolutionDTO` (a solução, com `position`
  e `code`), e a revisão confere que o termo de base de cada um está no glossário. Entram no front
  `FactsLine`, `CodeBlock`, o diálogo largo (`size="wide"`), `KnowledgeComponentMatrix`,
  `ProblemStatementsTable`, `KnowledgeComponentOriginDialog`, `NewKnowledgeComponentDialog` e
  `ReopenApprovalDialog`, como o nome no código de um termo do desenho (linha de fatos, bloco de
  código, matriz, aba Problemas, origem do conceito, Novo conceito e aviso de reabrir). Mudam o
  `Problem` (`:30`), o `KnowledgeComponent` (`:36`), o `CandidateKnowledgeComponent` (`:37`, com o
  rótulo Justificativa do modelo de linguagem da `translated_reasoning`), o `kc_draft` e o
  `kc_approved` (`:80-81`), o `GeneratedByLLM` (`:125`), a linha de fatos e a recorrência
  (`:126-127`), a origem do conceito e o problema sem conceito (`:150-151`) e as rotas (`:247-248`,
  `:260-264`). A rota de mesclar (`:263`) sai.
- `DECISIONS.md`. Entram os porquês do marcador pelo `updated_at` do `kc` e do renomear sem efeito
  (K). A coluna segue o padrão `updated_at`, e outra entidade que precisar dele ganha o mesmo nome.
  O marcador lê o `updated_at` porque hoje o renomear é a única edição do `kc`, e uma edição nova
  do `kc` que não seja do nome precisa rever o marcador. Entram também os porquês da rota da origem
  com uma chamada por conceito e do diálogo de 760px (I), da tradução que fica (Q), do bloqueio na
  tela e no backend (J), do conceito novo com ao menos um problema (L, com o 422 da validação), do
  aviso de reabrir (M), da ordem fixa da matriz, porque a linha que pula de lugar debaixo do mouse
  desorienta (N), da data da extração (S) e das duas exceções à linha de 32px (N e O). E as
  decisões de engenharia que o comentário de uma linha não comporta. O balão que nasce no
  `dialog[open]`, porque o diálogo modal fica na camada de cima. A contagem e o código das soluções
  pelo `ISubmissionRepository`, porque a `classroom_import` é a dona da `submission`. O fio da
  coluna presa só com rolagem. Mudam o nome gerado e o mostrado (`:205-207`), a descrição deduzida
  (`:305-309`), os formulários de um campo (`:476-477`), a lista invertida com a ordem nova
  (`:509-512`), o exercício treinado (`:514-516`), o xis que vira a célula (`:522-524`), a barra de
  ação (`:531-534`), as dicas de hover (`:603-606`), a matriz pensada para 15 conceitos
  (`:707-712`), a origem (`:717-725`), as estrelas (`:737-741`) e o Aprovar (`:743-745`). A fusão
  que guarda o histórico (`:321-322`) sai.
- `DESIGN.md`. Mudam Botões, com o compacto primário na faixa das abas (`:106-109`), Diálogo, com as
  duas larguras, a altura máxima e o aviso (`:137-138`), Marcadores de modelo (`:182-189`), Dica e
  balão, com o título opcional (`:191-194`), Bloco de código (`:196-198`), Matriz, com a ordem fixa
  (`:200-203`), Origem do conceito (`:205-208`), Ícones (`:236`, `:238`), Tabelas, com as duas
  exceções aos 32px e o fio da coluna presa só com rolagem (`:253-256`), Conceitos (`:343-361`) e o
  Estado (`:10-12`), que passa a dizer que a Conceitos está em obra por este plano. A versão e a
  página ficam para a etapa 2.
- Nenhum documento cita commit que ainda não existe, e os commits entram no fechamento.
- Critério de pronto. Nenhum código muda. A busca por descrição, mesclar, merge e description nos
  `docs/` só acha o histórico e os planos concluídos. A conferência de estilo dos documentos, em
  Verificação, não acha nada nas linhas novas, e a revisão confere o registro contra as decisões.

### 1. Linha de base visual, sem commit

- O roteiro de captura, escrito no scratchpad da sessão e fora do repositório, como decidiu a base.
  Node 22 do host com o WebSocket nativo, o Chrome do flatpak sem janela e o domínio Fetch. O GET
  passa à api real, todo outro método é bloqueado, e as fontes do Google passam.
- Captura a Conceitos de hoje em 1500px e 1100px, no rascunho (A439 da turma 6), no treinado (A439
  da turma 1), no pronto para conceitos e em statistics_only (simulado se o banco não tiver um), com
  os diálogos de renomear, remover, desligar e mesclar abertos e sem confirmar.
- Captura também as telas que usam as peças compartilhadas que mudam nas etapas 8 e 11, como fez a
  linha de base do `FRONTEND_BASE_PLAN.md` (`:100-107`). São Turmas, com a `DataTable` do
  `ClassroomTable` e os diálogos de nome e de exclusão abertos (`ClassroomNameDialog`,
  `RemoveClassroomDialog`), a Turma, o menu com o balão do `SideMenu` e a Análise, com o balão do
  `Histogram`, as abas e o diálogo do treino aberto e sem confirmar (`TrainingDialog`). O
  `ExtractionDialog` entra pelo pronto para conceitos. Importar dados fica de fora, porque nenhuma
  peça que a tela usa muda nas etapas 8 e 11, e o `Button` dela não muda mais (J).
- Confere no diálogo do aluno da Análise (A439 da turma 1) se o balão do `InfoHint` e do
  `GeneratedByML` aparece. O resultado vai para o Estado, e a etapa 8 confere o mesmo diálogo depois
  do conserto do portal.
- Os logs da api confirmam zero escritas.

### 2. A página de referência v6 (V)

- `git mv docs/design/design-system-v5.html docs/design/design-system-v6.html`, com as referências
  no mesmo commit (`DESIGN.md:8`, `IMPLEMENTATION_PLAN.md:27` e `:200`). O
  `FRONTEND_BASE_PLAN.md:98` fica como está, porque é plano concluído e cita a página que existia
  quando foi escrito. O `DESIGN.md:7-8` passa a "Versão 6, 08/10/2026", e a tabela de Versões ganha
  a linha 6, com o link da maquete e a ressalva de que as organizações B e C e o Aprovar que some
  foram superados.
- Na página mudam o título e a data (`:6`, `:443`) e a frase do `tokens.css` não migrado, que já é
  falsa (`:444`). Entra um bloco de CSS das peças da versão 6. Os espécimes são refeitos com um
  recorte real do A439 da turma 6, tirado do retrato descrito em Verificação, sem número inventado.
  São o marcador com um nome em pt-BR (`:659-664`), o bloco de código com as abas Solução e o
  trecho destacado (`:666-671`), os ícones (`:734`, `:740`), as tabelas (`:745`), a Conceitos
  (`:835-855`), a origem (`:857-873`), as Versões (`:917-923`) e os dados do script
  (`:1107-1126`). A Conceitos
  ganha a matriz ordenada com a coluna presa, a aba Problemas com o enunciado e espécimes novos do
  aprovado, do problema sem conceito, do Novo conceito e do aviso de reabrir.
- Critério de pronto. A página abre no Chrome sem janela, sem erro no console, em 1500px e 1100px.
  Nenhum espécime usa o nome em inglês nem a descrição, e a revisão confere cada espécime contra as
  decisões.

### 3. Mesclar sai (F)

- Backend. No controller saem os imports dos dois DTOs (`knowledge_components_controller.py:17-18`),
  o do caso de uso (`:38-40`) e a rota `POST /merge` (`:128-135`). No `dependencies.py` saem o
  import (`:26-28`) e a fábrica (`:170-178`). Saem o `merge_knowledge_components_use_case.py`, os
  `MergeKnowledgeComponentsDTO` e `MergedKnowledgeComponentsDTO`
  (`edit_knowledge_components_dto.py:29-32`, `:59-61`) e o `move_bindings` da interface
  (`problem_knowledge_component_repository.py:22-26`) e da implementação
  (`sqlite_problem_knowledge_component_repository.py:57-71`). Saem também as duas regras que só o
  mesclar usa, `knowledge_components_are_distinct_rule.py` e
  `knowledge_components_belong_to_assignment_rule.py`. O comentário "O corpo do PATCH"
  (`edit_knowledge_components_dto.py:15`) passa a PUT, porque a rota é PUT (`:107` do controller).
- Front. Saem o `MergeKnowledgeComponentsDialog.tsx`, o botão de mesclar do
  `KnowledgeComponentsCard` (`:63-68`), o `useMergeKnowledgeComponents`
  (`api/knowledgeComponents.ts:112-123`), o `mergedProblemIds` (`knowledgeComponents.ts:38-41`) e o
  caso de mesclar no estado dos diálogos do editor (`KnowledgeComponentEditor.tsx:26-30`). O
  `SelectField` fica, porque a importação o usa.
- O `schema.d.ts` é regerado e perde a rota e os dois DTOs.
- Testes. Saem os quatro do mesclar no controller, pelo nome, `test_merge_unions_bindings`
  (`knowledge_components_controller_test.py:120`), `test_merge_rejects_cross_assignment_kc`
  (`:157`), `test_merge_rejects_keep_from_other_assignment` (`:180`) e
  `test_merge_self_merge_rejected` (`:196`). O `test_remove_that_empties_a_problem_is_blocked`
  (`:142-154`), que fica no meio deles, não é do mesclar e fica, porque é a única cobertura do
  `DELETE /knowledge-components/{id}` recusado com o rollback
  (`remove_knowledge_component_use_case.py:52-54`). Saem também os três das regras órfãs
  (`knowledge_component_rules_test.py:50-72`) com os imports, o do `mergedProblemIds`
  (`knowledgeComponents.test.ts:47-53`) e o da página (`KnowledgeComponentsPage.test.tsx:326-341`).
  O `test_bindings_union_on_move_and_ignore_duplicates` (`sqlite_repositories_test.py:68-86`) sai, e
  entra um teste menor só do `OR IGNORE` do `bind_problems` com um problema repetido
  (`sqlite_problem_knowledge_component_repository.py:40-47`), porque era a única cobertura dele.
- Critério de pronto. A suíte e o gate passam. Em `src/` e `tests/`, fora do `schema.d.ts`, a busca
  por `Merge[A-Z]`, `onMerge`, `merge_knowledge`, `/merge`, `mesclar`, `move_bindings`,
  `KnowledgeComponentsAreDistinct` e `KnowledgeComponentsBelongToAssignment` não acha nada, e a
  busca por `merge` sem distinção de caixa só acha o `mergeProblems` e o `mergeConcepts` da Análise
  (`mastery_dashboard/dashboard.ts:42`, `:64`, o `dashboard.test.ts` e o `AnalysisCard.tsx`), que
  juntam a estatística e o domínio e ficam.

### 4. Renomear com data, o marcador e as regras de edição (J, K, L)

- `0021_kc_updated_at.sql`, com `ALTER TABLE kc ADD COLUMN updated_at TEXT`.
- A entidade ganha `updated_at: str | None` e `is_generated_by_llm`
  (`knowledge_component_entity.py:15`). O repositório lê a coluna no `_to_entity` e nos dois
  SELECTs (`sqlite_knowledge_component_repository.py:9-16`, `:37`, `:45`), e o `rename` passa a
  `rename(kc_id, name, updated_at)` na interface (`knowledge_component_repository.py:16`) e na
  implementação (`:51-55`). O `remove` (`:57-61`) continua gravando só o `deleted_at`. O
  `RenameKnowledgeComponentUseCase` (`:34-42`) ganha a saída sem efeito do mesmo nome e grava
  `updated_at = utc_now_iso()` nos outros casos.
- O `KnowledgeComponentDTO` ganha `is_generated_by_llm` nos três pontos que o montam, e a rota da
  tela lê o marcador das entidades (`list_problem_knowledge_components_use_case.py:39-41`).
- A `EveryProblemHasAKnowledgeComponentRule` entra, calada sem exercício e sem nenhum conceito, e o
  `ApproveKnowledgeComponentsUseCase` ganha no construtor o `IProblemRepository` e o
  `IProblemKnowledgeComponentRepository` e a regra nova no `rules()`
  (`approve_knowledge_components_use_case.py:26-40`). A fábrica do `dependencies.py` (`:181-188`)
  monta os dois repositórios.
- O `problem_ids` do `AddKnowledgeComponentDTO` (`edit_knowledge_components_dto.py:12`) fica
  obrigatório com ao menos um item, pelo `Field(min_length=1)` de L.
- O `schema.d.ts` é regerado, e as fixtures do front ganham `is_generated_by_llm`
  (`knowledgeComponents.test.ts`, `KnowledgeComponentsPage.test.tsx`).
- O `_seed_kc` do teste do controller (`knowledge_components_controller_test.py:31-34`) ganha o
  `generated_name`, que a entidade já tem (`knowledge_component_entity.py:15`), para os testes do
  marcador semearem um conceito gerado. A função de fixture da extração só nasce na etapa 5a.
- Testes. A migração no padrão do `test_migration_0020` (`migrations_test.py:539`), com o
  `updated_at` vazio na linha que já existia. Os dois testes que chamam o `rename` com dois
  argumentos (`sqlite_repositories_test.py:58`, `:142`) passam a mandar a data e a conferir o
  `updated_at`, e o primeiro confere também que o `remove` deixa o `updated_at` como estava. Um
  `knowledge_component_entity_test.py` novo, com a propriedade. No controller, o rename grava
  `updated_at` e o marcador some da rota da tela, o mesmo nome responde 200, deixa o `updated_at`
  vazio e mantém `kc_approved`, e o mesmo nome no treinado continua 409. A rota da tela
  traz o marcador num conceito gerado e não o traz num renomeado nem num criado pelo professor. A
  regra nova com fakes em memória, no padrão de `knowledge_component_rules_test.py:97-102`, calada
  sem exercício e sem conceito, e no controller o rascunho com um problema sem conceito dá 409, o
  texto cita o problema e a situação continua `kc_draft`. Um rascunho com problemas e nenhum
  conceito recebe só a mensagem de hoje ("assignment não tem nenhum KC para aprovar"), sem a lista
  dos problemas, e os testes de hoje do aprovar passam sem mudança (`:211-241`). O POST com a lista
  vazia dá 422, e sem o campo também, e entram os casos que hoje nenhum teste cobre, o 201 com os
  vínculos, o aprovado que volta a rascunho, o treinado com 409 e o problema de outro exercício com
  409.
- Critério de pronto. A suíte e o gate passam com o schema novo, e a tela de hoje continua igual.
  A única diferença é o Aprovar de um exercício com problema sem conceito, que o `ApprovalBar` de
  hoje deixa clicar e que passa a mostrar a recusa do backend pelo `editErrorText`.

### 5a. A rota da tela devolve o enunciado, a contagem e a data (J, O, S)

A etapa 5 se divide em duas, para a parte que apaga dado ficar num commit próprio, que pode ser
segurado ou revertido sozinho. A 5a só acrescenta ao contrato.

- O `ISubmissionRepository` ganha `count_correct_runs_by_problem(assignment_id)` na interface
  (`submission_repository.py:10-25`) e na implementação, depois do `list_correct_runs()`
  (`sqlite_submission_repository.py:79-88`), com o `AND problem_id IS NOT NULL`.
- O repositório do job ganha `find_latest_done(assignment_id)`, com
  `status = 'done' ORDER BY updated_at DESC, id DESC LIMIT 1`, e um `_to_entity` tirado do `get`
  (`sqlite_kc_generation_job_repository.py:23-45`) para os dois usarem.
- O `ProblemKnowledgeComponentsDTO` (`list_problem_knowledge_components_dto.py:13-16`) ganha
  `statement` e `correct_run_count`, ao lado da `description`, que sai na 5b. O
  `ListProblemKnowledgeComponentsResponseDTO` (`:19-22`) ganha `extracted_at`, nulo sem job
  concluído. O caso de uso ganha no construtor o `ISubmissionRepository` e o
  `IKnowledgeComponentGenerationJobRepository`, e a fábrica
  (`assignments/problems/presentation/dependencies.py:36-44`) monta os dois.
- Front. As fixtures ganham `statement`, `correct_run_count` e `extracted_at`, e o `schema.d.ts` é
  regerado. A tela não muda.
- Testes. A função nova de `tests/fixtures/knowledge_components.py` semeia execuções corretas e
  incorretas e um `kc_job` concluído. No `problems_controller_test.py`, o `_seed` (`:8-16`) grava
  também o enunciado, e o teste da rota da tela
  (`test_problem_kcs_route_joins_problems_and_kcs_including_problems_without_kc`, `:50`) confere o
  enunciado e a contagem. No controller, a contagem dá 0 no problema sem acerto e o `extracted_at`
  vem nulo sem job concluído. No repositório da execução, a contagem ignora as incorretas e o
  `Compile.Error`, ignora a execução correta sem problema e fica no próprio exercício. No do job, o
  `find_latest_done()` devolve nulo sem job, ignora o que roda e o que falhou, escolhe o mais
  recente entre dois concluídos e ignora outro exercício.
- Critério de pronto. A suíte e o gate passam com o schema novo, e a tela de hoje continua igual.

### 5b. A descrição sai (O)

- `0022_drop_problem_description.sql`, com `ALTER TABLE problem DROP COLUMN description`. Mudam a
  entidade (`problem_entity.py:12`), o repositório (`sqlite_problem_repository.py:16-18`, `:23`,
  `:28`), o `ProblemDTO` (`list_problems_dto.py:10`), o `list_problems_use_case.py` (`:1`, `:24`),
  as descrições das rotas (`problems_controller.py:25`, `:37`), o comentário do caso de uso da rota
  da tela (`:1`) e o do pacote, "a descrição que o LLM deduz de cada um"
  (`assignments/problems/__init__.py:1`). A `description` sai do `ProblemKnowledgeComponentsDTO`.
- Front. O `ProblemsCard` mostra o enunciado no lugar da descrição (`ProblemsCard.tsx:24-26`), com a
  classe renomeada, até sair na etapa 9c, e as fixtures perdem a `description`. O `schema.d.ts` é
  regerado.
- Testes. O teste da `0022` migra até a 21 e semeia um problema com descrição e enunciado e uma
  linha em cada uma das quatro tabelas que apontam para `problem`, a `submission`, a `problem_kc`, a
  `sampled_solution`, que pede uma `submission`, e a `candidate_kc`, que pede um `kc`, mais uma
  `kc_evidence`. Depois migra até a 22 e confere o `user_version`, a coluna fora, o enunciado
  preservado, as cinco linhas filhas intactas e o `foreign_key_check` vazio. O
  `test_migration_0011`, que lê a `description`, continua, porque migra só até a 11
  (`migrations_test.py:272-281`). No `problems_controller_test.py`, o `_seed` deixa de gravar a
  descrição, o `test_the_problems_route_lists_every_problem_with_its_description` (`:19`) vira
  `test_the_problems_route_lists_every_problem` e confere só o `problem_id`, e o teste da rota da
  tela (`:60`) deixa de ler a `description`. O
  `test_the_problems_come_back_ordered_and_without_description`
  (`sqlite_problem_repository_test.py:17`) muda de nome.
- Critério de pronto. A suíte e o gate passam. No backend, a busca por `description` e por
  `descrição` em `src/` e `tests/` só acha o `description=` das rotas do FastAPI, o teste da
  migração `0011` (`migrations_test.py:362`), o teste da `0022` e as migrações antigas. No front,
  fora do `schema.d.ts` e do `package-lock.json`, a busca por `description` só acha a prop do
  `PageHeader` e quem a usa, e no `schema.d.ts` nenhum dos dois DTOs de problema tem o campo.

### 6. A origem do conceito no backend (I, P)

- O `ISubmissionRepository` ganha `get_codes(submission_ids)`, que devolve o código de cada execução
  com o `\r\n` e as tabulações intactos e ignora o id que não existe.
- `get_knowledge_component_origin_dto.py`, com o `KnowledgeComponentOriginDTO` (`kc_id`, `name`,
  `is_generated_by_llm` e os problemas), o `ProblemOriginDTO` (`problem_id`, `statement`, as
  justificativas traduzidas, o trecho ou nulo e as soluções), o `KnowledgeComponentEvidenceDTO`
  (`position`, `first_line` e `last_line`) e o `SampledSolutionDTO` (`position` e `code`). Sem o
  `generated_name` e sem a justificativa em inglês (P), e sem campo para as extrações antigas (X).
- `get_knowledge_component_origin_use_case.py`. Confere o conceito pelo
  `get_active_knowledge_component()`, pega os problemas dele em ordem, porque o `problems_of()` não
  ordena (`sqlite_problem_knowledge_component_repository.py:87-92`), e junta os enunciados, os
  candidatos na ordem da posição, os trechos e as soluções do problema. A justificativa traduzida
  nula sai da lista.
- A rota `GET /knowledge-components/{kc_id}/origin` no controller, com `response_model` e
  `description`. Ela não colide com `/generation-jobs/{job_id}` (`:89-96`), porque o segundo
  segmento é o literal. A fábrica nova monta os repositórios, todos já importados no
  `dependencies.py`.
- A função de fixture da etapa 5a passa a semear também as soluções amostradas, os candidatos e os
  trechos. O `schema.d.ts` é regerado, com a rota nova e sem mudança no front.
- Testes. O conceito gerado traz as justificativas, o trecho e as cinco soluções na ordem da
  posição, com o `\r\n` intacto. Um par com duas justificativas. Um vínculo do professor, sem
  justificativa e sem trecho, com as soluções do problema. Um trecho descartado, com justificativa
  e sem trecho. Desligar e religar mantém o trecho, e o par desligado não aparece. O problema sem
  enunciado dá `statement` nulo. Uma justificativa traduzida nula sai da lista, sem erro. Um
  problema sem execução correta, ligado pelo professor num exercício de extração nova, vem com a
  lista de soluções vazia. 404 para o conceito que não existe, o removido e o de exercício
  removido. No repositório, o `get_codes()`.
- Critério de pronto. A suíte e o gate passam, e o `lint-imports` mantém os 12 contratos.
- Aqui o backend está completo, e a api é recriada antes do front (W), pela sequência da seção
  "Depois do plano, com o Leo".

### 7. O cabeçalho (A, S)

- `components/FactsLine.tsx`, com os itens em ordem, a vírgula como texto e um item de alerta com
  `CircleAlert` em `--color-danger` e o texto em `--color-danger-text` 600. O `PageHeader` ganha o
  encaixe `facts` abaixo da linha do título (`PageHeader.tsx:19-22`), e a `description` fica, porque
  as outras telas a usam.
- O título passa ao nome do exercício (hoje "Conceitos", `KnowledgeComponentsPage.tsx:57`), e saem o
  `DESCRIPTION` e a `description` (`:15-16`, `:65`). A consulta da rota da tela mora no
  `AssignmentWorkspace` (`:15`) e não sobe para a página, porque a página só conhece o exercício
  depois dos retornos antecipados (`:29-41`), e um hook não vem depois de um retorno. O
  `PageHeader` desce para o `AssignmentWorkspace`, mas fica antes e fora do `QueryStates`
  (`:30`), com o título e a etiqueta que já vêm do `assignment`. Assim o h1 e a etiqueta aparecem
  no mesmo render do caminho, e o teste de hoje que lê a etiqueta logo depois do caminho
  (`KnowledgeComponentsPage.test.tsx:106-113`) continua síncrono. A linha de fatos entra pelo
  encaixe `facts` quando `query.data` existe.
- Os fatos são problemas, conceitos, "extraídos em" com o `formatDate()` (`lib/format.ts:26-28`)
  e os problemas sem conceito ou "nenhum problema sem conceito". O "extraídos em" some quando o
  `extracted_at` é nulo, porque o `formatDate()` não trata o nulo. Sem conceitos, só os problemas.
  O `ApprovalBar` fica até a etapa 9a.
- As contagens e a lista dos problemas sem conceito saem de funções puras em
  `knowledgeComponents.ts`.
- Testes. `FactsLine.test.tsx` com a ordem, a vírgula e o alerta. Um caso do `PageHeader` com
  `facts`. Na página, o h1 "Assignment 439" e a linha de fatos com e sem problema sem conceito, com
  a data da fixture ao meio-dia UTC, e sem o "extraídos em" quando o `extracted_at` é nulo. O teste
  do caminho e da etiqueta (`:106-113`) passa sem mudança.
- Critério de pronto. O gate passa, e a captura em 1500px e 1100px mostra o cabeçalho novo sobre o
  resto da tela de hoje.

### 8. As peças da matriz e do balão (G, J, N, O)

- `components/GeneratedByLLM.tsx`, no molde do `GeneratedByML` (`GeneratedByML.tsx:6-17`), com as
  quatro variantes de tamanho.
- `Tabs`. A raiz vira um invólucro com a `tablist` dentro, as ações à direita e o rótulo à
  esquerda fora da `tablist` e com `aria-hidden` (hoje a raiz é a própria `tablist`,
  `Tabs.tsx:19-36`). O item de aba ganha `ariaLabel`. A Análise não muda de uso
  (`AnalysisCard.tsx:50`).
- `DataTable` com o layout fixo, a primeira coluna presa com fundo `--color-surface` e o fio só
  com rolagem (a classe `is-scrolled` no `onScroll` do invólucro), as classes de célula que quebra
  linha e que alinha à esquerda e a variante do `ColumnLabel` que ocupa a largura da célula, sem o
  teto de 150px (`DataTable.css:65-71`). A largura mínima continua com quem usa
  (`DataTable.tsx:10`, `:18`).
- `Tooltip` com o `size` largo, o título opcional, o `white-space: pre-line` e o portal no diálogo
  aberto mais próximo.
- Testes. `GeneratedByLLM.test.tsx` no molde do `GeneratedByML.test.tsx:7-14`, com cada variante. No
  `ui.test.tsx`, as ações fora da `tablist` e o nome da aba pelo `ariaLabel`, as classes da
  `DataTable`, o rótulo sem teto e a classe `is-scrolled`, que liga com o `scrollLeft` acima de 0 e
  desliga ao voltar. No
  `Tooltip.test.tsx`, o balão nasce dentro do diálogo aberto, o largo e o título com o texto em
  dois parágrafos. Os testes de hoje continuam (`ui.test.tsx:12-44`, `Tooltip.test.tsx:7-34`,
  `MasteryDashboardPage.test.tsx:247`, `:254`).
- Critério de pronto. O gate passa, e o balão aparece no diálogo do aluno. Na captura, a Análise,
  com as abas, o balão do histograma e o diálogo do treino, Turmas com a tabela e o menu com o
  balão ficam iguais à linha de base da etapa 1.

### 9a. O cartão com as abas e a matriz (B, C, D, F, J, N, U)

A etapa 9 se divide em três, cada uma num commit que deixa a tela funcionando, porque ela cria três
componentes, apaga quatro e reescreve a maior parte do teste da página. A 9a troca a organização,
a 9b o jeito de criar um conceito e a 9c a aba Problemas.

- O `KnowledgeComponentEditor` vira o cartão com as abas Conceitos por problema (`Blocks`) e
  Problemas (`FileCode`). Na aba da matriz e com o exercício editável, a ação é Aprovar conceitos
  (primário compacto), e o Novo conceito entra na 9b. O Aprovar habilita em `kc_draft` sem problema
  vazio e fica só desabilitado, com o `disabled` nativo e sem balão, quando há problema vazio e em
  `kc_approved` (J, M). O rodapé do cartão traz a frase de apoio no rascunho, a de consulta no
  treinado e nada com os conceitos aprovados (U). O estado dos diálogos guarda ids, e o editor
  guarda a lista de ids da ordem fixa (N).
- Até a 9c, a aba Problemas mostra a lista do `ProblemsCard` de hoje, sem o `Card` de fora, com o
  Adicionar por problema, que é o jeito de criar um conceito até a 9b.
- `KnowledgeComponentMatrix.tsx`. A `DataTable` com o layout fixo e a primeira coluna presa. No
  cabeçalho, Conceito, um número por problema em `.num` com sublinhado pontilhado, foco pelo
  teclado e o balão largo com o título "Problema N" e o enunciado ou "Sem enunciado.", Recorrência
  e a coluna das ações. O problema sem conceito fica em `--color-danger-text` com `CircleAlert`, e
  o balão dele tem o título "Problema N sem conceito", o motivo, que depende da contagem de
  execuções corretas, e, depois de uma linha em branco, o enunciado, quando há (J). Na linha, a
  célula do nome é o flex com o rótulo que ocupa a célula, cortado com reticências e com o balão, e
  o `GeneratedByLLM` de 20px depois dele, sempre à vista. A célula de vínculo é um botão de 20px
  com `aria-pressed` e o nome "<conceito> no problema <N>", em `--color-observed` e desabilitada no
  treinado. A recorrência é "N de M". As
  ações são o lápis e a lixeira, com os nomes de hoje (`KnowledgeComponentsCard.tsx:57-73`), e a
  lupa entra na etapa 11. A última linha traz os conceitos por problema, com o 0 em vermelho e o
  ícone. A largura mínima é de 220px mais 48px por problema mais a recorrência e as ações.
- O clique na célula vazia liga (`useLinkKnowledgeComponent`). Na ligada, uma função pura decide
  entre recusar, confirmar e desligar direto, a regra de hoje
  (`KnowledgeComponentEditor.tsx:56-66`). O `UnlinkTarget` passa a guardar só o id e o nome do
  conceito (`UnlinkKnowledgeComponentDialog.tsx:9-14`).
- Treinado, sem ações nas abas e sem a coluna das ações até a lupa. O aviso de treinado de hoje
  (`KnowledgeComponentEditor.tsx:70-75`) vai para o rodapé do cartão (U). O aviso de
  aprovado (`:76-81`) fica até a etapa 10, porque é ele que avisa que editar reabre a aprovação
  enquanto o `ReopenApprovalDialog` não existe.
- Saem o `ApprovalBar`, com a frase "N de M exercícios aprovados" (`ApprovalBar.tsx:25`) e a conta
  dos aprovados na página (`KnowledgeComponentsPage.tsx:42-44`), o `KnowledgeComponentsCard`, o
  layout de duas colunas e o `.kc-editor__error` do CSS. O erro do aprovar passa à
  `OutcomeMessage` do cartão.
- O `knowledgeComponentsOf()` passa a ordenar por recorrência decrescente, nome em pt-BR e id
  (hoje só pelo nome, `knowledgeComponents.ts:25`), que é a ordem da primeira carga. Entram a
  `stableKnowledgeComponentOrder(previousIds, knowledgeComponents)`, que mantém a posição dos que
  já estavam, põe o novo no fim e tira o removido (N), e a função pura do desfecho do clique.
- Testes. Na página são reescritos o treinado (`:132-141`), o desligar pelos botões das etiquetas
  (`:175-196`, `:231-265`), que passa às células da matriz, e o aprovar (`:343-352`). Entram a ordem
  das linhas, a linha que não muda de lugar depois de uma edição que mudaria a recorrência, ligar
  pelo clique, o 0 em vermelho, o balão do número com o título e o enunciado e o do problema sem
  conceito com cada motivo e o enunciado, as células desabilitadas no treinado e o Aprovar
  desabilitado com problema sem conceito. Em `knowledgeComponents.test.ts`, a ordem com empate
  (hoje `:20-31`), a ordem fixa, com o conceito que fica no lugar, o novo no fim e o removido fora,
  e o desfecho do clique.
- Critério de pronto. O gate e a suíte passam. A captura em 1500px e 1100px mostra o rascunho, o
  problema sem conceito (simulado), o aprovado (simulado), com o aviso de hoje, e o treinado, a
  página sem rolagem lateral e a matriz rolando dentro do invólucro com a primeira coluna presa e o
  fio só com rolagem.

### 9b. O Novo conceito (L, T, U)

- `NewKnowledgeComponentDialog.tsx`, no lugar do `AddKnowledgeComponentDialog`, aberto pelo Novo
  conceito (secundário compacto, `Plus`) à esquerda do Aprovar, na aba da matriz e com o exercício
  editável. O campo Nome e um `fieldset` Problemas com uma caixa por problema, com o número, o
  começo do enunciado em duas linhas e a contagem de conceitos ou "sem conceito" em vermelho. A
  lista rola por dentro acima de 260px, como na maquete (`screen.css:180-186`). Criar fica
  desabilitado até ter nome e um problema. O nome repetido é recusado só no front, como hoje, pelo
  `normalize` (`AddKnowledgeComponentDialog.tsx:40-46`, `:72-73`), agora com o erro no campo "Já
  existe um conceito com este nome." O `useCreateKnowledgeComponent` passa a receber o nome e os
  problemas (`api/knowledgeComponents.ts:64-75`). Cada caixa mostra só o número do problema (T).
- As notas das estrelas (U). O Novo conceito diz "O conceito novo nasce sem
  estrelas, porque o nome é seu." (`screen.js:652`). O `RenameKnowledgeComponentDialog` diz, só
  quando o conceito é `is_generated_by_llm`, "O nome atual veio do modelo de linguagem. Ao salvar,
  o nome passa a ser seu e as estrelas saem." (`screen.js:552-554`).
- O Adicionar sai da lista da aba Problemas, e saem o `AddKnowledgeComponentDialog` e as classes de
  `KnowledgeComponentDialogs.css` que só ele usava (`:1-19`, `:33-87`). Entra a função pura do nome
  normalizado.
- Testes. Na página, o adicionar (`:267-298`) dá lugar ao Novo conceito, com o Criar desabilitado
  sem nome ou sem problema, o nome repetido e o corpo com os problemas marcados. A nota do Novo
  conceito, e a do renomear num conceito gerado e não num criado pelo professor.
- Critério de pronto. O gate e a suíte passam, e a captura mostra o Novo conceito aberto, com e sem
  o erro do nome, e o renomear de um conceito gerado.

### 9c. A aba Problemas e o pronto para conceitos (E, F, O, T)

- `ProblemStatementsTable.tsx`, com Problema, Enunciado e Conceitos, no lugar da lista do
  `ProblemsCard`. O enunciado fica à esquerda e quebra linha, sem estrelas, "sem enunciado" em
  `.data-table__missing` e o 0 em vermelho. A coluna Problema mostra só o número (T).
- Pronto para conceitos, o ícone `Sparkles` vira `Blocks` e o cartão perde o título
  (`AssignmentWorkspace.tsx:1`, `:39`, `:42`).
- Saem o `ProblemsCard` e o `ProblemsCard.css`, com as etiquetas e o xis de desligar, que a matriz
  substituiu.
- Testes. Na página, a aba Problemas com o enunciado e o "sem enunciado", o 0 em vermelho e o
  pronto para conceitos com os blocos. Nenhum teste da página procura mais as etiquetas.
- Critério de pronto. O gate e a suíte passam. A captura em 1500px e 1100px mostra o rascunho, o
  problema sem conceito (simulado), o aprovado (simulado), o treinado, a aba Problemas e o pronto
  para conceitos.

### 10. O aviso de reabrir a aprovação (M)

- `ReopenApprovalDialog.tsx`, no tom neutro, porque não é exclusão, com Cancelar e a ação de seguir.
  Ele recebe a edição pendente por ids (ligar ou desligar, o conceito e o problema) e, ao seguir,
  dispara a mutação e fecha. Abre no clique da célula em `kc_approved`, antes de ligar ou de
  desligar direto. A recusa do problema vazio continua sem aviso, porque nada muda.
- Nas confirmações de remover e de tirar o último problema do conceito, o aviso entra como uma
  linha no próprio diálogo (M). No renomear e no Novo conceito, o aviso é a mesma linha dentro do
  formulário, acima dos botões (M). O texto mora numa constante em `knowledgeComponents.ts`.
- Sai o aviso de aprovado acima do cartão (`KnowledgeComponentEditor.tsx:76-81`), que o
  `ReopenApprovalDialog` e as linhas substituem.
- Não há estado de "já avisei". A primeira edição devolve o exercício a `kc_draft` no backend
  (`revert_approval_after_edit`, por exemplo `add_problem_knowledge_component_use_case.py:91`), e a
  recarga muda a situação.
- Testes. Com um exercício aprovado na fixture, o Aprovar fica desabilitado, o clique na célula
  abre o aviso, Cancelar não chama a api, seguir chama o POST ou o DELETE, e as confirmações de
  remover e de tirar o último problema mostram a linha, como o renomear e o Novo conceito. O aviso
  de aprovado acima do cartão não aparece mais.
- Critério de pronto. O gate e a suíte passam, e a captura do aprovado simulado mostra o aviso
  aberto. O clique em seguir, na captura, só confere a mensagem de erro, porque o roteiro bloqueia o
  POST.

### 11. A origem do conceito no front (H, I, P, X)

- `Dialog` com o `size` largo de 760px, um encaixe logo depois do título e fora do `h2` e um encaixe
  da linha de fatos. Em todos os tamanhos, a altura máxima de `calc(100vh - 48px)`, com o cabeçalho
  e o rodapé presos e o corpo rolando por dentro (hoje 440px e sem altura máxima, `Dialog.css:1-9`).
- `components/ui/CodeBlock.tsx`. As abas presas ao topo (`tablist`), a grade número e texto, a
  numeração em `--color-text-disabled`, as linhas destacadas com o número em `--color-model-strong`
  600, tab-size 4, `white-space: pre` e rolagem nos dois sentidos dentro do bloco. Separa o código
  por `\r\n` ou `\n` e tira a última linha vazia. Recebe as soluções, o destaque, a aba inicial e o
  marcador de cada aba, e só desenha o painel ativo. Ao mostrar um painel com destaque, o bloco rola
  por dentro até a primeira linha destacada, sem mexer na página, como a maquete aprovada
  (`base.js:515-522`), por um `useEffect` novo, que entra na lista do `ARCHITECTURE.md`. Quem usa o
  `CodeBlock` não o desenha sem solução.
- `KnowledgeComponentOriginDialog.tsx`, aberto pela lupa, que entra na coluna das ações com o nome
  "Ver a origem de <conceito>", também no treinado. O título é o nome do conceito, com o
  `GeneratedByLLM` de 24px só quando `is_generated_by_llm`. A linha de fatos diz "aparece em N de M
  problemas", com o M da consulta da tela. O conteúdo fica dentro dos estados de carregando e de
  erro com tentar de novo. Na fileira, o rótulo "Problema" com `FileCode` uma vez e cada aba só com
  o identificador, com o nome acessível "Problema N". O painel tem `key` pelo problema, para o bloco
  nascer na aba certa, e mostra os três blocos de I, com as dicas da maquete e com o rótulo
  "Justificativa do modelo de linguagem". O problema sem solução amostrada mostra a frase de X no
  lugar do `CodeBlock`. O rodapé tem Fechar. Nunca o `generated_name` nem a justificativa em
  inglês.
- `useKnowledgeComponentOrigin(kcId)` com a chave própria em `knowledgeComponentKeys`, e o
  `useRefreshAssignment` (`api/knowledgeComponents.ts:46-53`) também invalida a origem, porque
  ligar, desligar e renomear mudam o que ela mostra. Entra a função pura que classifica o painel
  (com trecho, trecho descartado e vínculo do professor).
- A dica das soluções evita a palavra justificativa (I).
- Testes. No `ui.test.tsx`, o diálogo largo, a altura máxima com o corpo rolando e o nome acessível
  sem o marcador. Um teste do `CodeBlock` com uma aba por solução, a aba inicial, as linhas
  destacadas, o `\r\n`, a troca de aba e a rolagem até o trecho. Na página, a lupa chama
  `GET /knowledge-components/{id}/origin`, as abas só com o identificador e o nome "Problema N", o
  enunciado e o "sem enunciado", a justificativa sob o rótulo
  "Justificativa do modelo de linguagem", a aba inicial do trecho, o vínculo do professor, o trecho
  descartado e o problema sem solução.
- Critério de pronto. O gate e a suíte passam. A captura mostra a origem de um conceito com trecho,
  do kc 54 com duas justificativas, do par 233 com o kc 48 descartado, de um vínculo do professor
  (simulado), de um problema sem enunciado (simulado), de um problema sem solução (simulado) e de
  um conceito do A439 treinado da turma 1, que é extração antiga e mostra todo vínculo como do
  professor (X), em 1500px e 1100px, com os balões das dicas e das estrelas à vista dentro do
  diálogo. Os diálogos das outras telas, capturados na
  etapa 1, ficam iguais à linha de base com a altura máxima nova.

### 12. Fechamento nos documentos

- `ARCHITECTURE.md`. Sai a frase da descrição (`:25`), entra a origem do conceito em
  `knowledge_components` (`:27`), o `CodeBlock` entre as primitivas (`:231`), o `GeneratedByLLM` e a
  `FactsLine` entre os componentes de produto (`:233`), o `useEffect` da rolagem do `CodeBlock` até
  o trecho (`:276-278`) e o caminho dos tipos sem a api no ar (`:304`).
- `IMPLEMENTATION_PLAN.md`. O Estado (`:7-9`), a linha v6 na tabela de versões, com o commit
  (`:15-21`), o `PageActionBar` só na importação (`:43-45`), os componentes novos (`:47-50`), as
  rotas (`:64`), o Estado da seção 4 (`:143-147`) e a linha da Conceitos da F5 (`:181`).
- `DEVELOPMENT.md`. A citação já errada do `DESIGN.md` (`:708`), a linha do aprovar
  (`:1009`), os commits da origem e dos problemas sem conceito (`:1011-1042`), o nome em inglês que
  não aparece (`:1025-1033`) e o commit na linha "9 e 11 a 17" (`:1049`). Nada disso muda o
  método.
- `DESIGN.md`. O Estado (`:10-14`) diz que a Conceitos está concluída por este plano, como o
  fechamento da base fez (`abe83c1`).
- A linha v6 da tabela de Versões do `DESIGN.md` e a do `IMPLEMENTATION_PLAN.md:15-21` citam
  commits que já existem, conferidos pelo `git log`.
- `GLOSSARY.md` com a conferência final. O `CLAUDE.md` do projeto não fica falso, e a conferência
  fica registrada. O Estado deste plano e a memória.
- Critério de pronto. A conferência de estilo dos documentos não acha nada nas linhas novas, e a
  revisão confere cada documento contra o código.

## Verificação

Em toda etapa que muda código, da 3 à 11, e na revisão final da tela, a suíte na `edmkt-core:dev`,
que já inclui o `code_comments_test`, o `architecture_test` e o import-linter
(`src/api/import_contracts_test.py`). Ela roda também nas etapas só de front, porque o
`code_comments_test` confere os comentários de TS, TSX e CSS do `src/web`
(`code_comments_test.py:21-31`, `:187-203`), e nem o `tsc`, nem o `eslint`, nem o `prettier` os
conferem. O `--user` evita arquivos de root no repositório.

```bash
docker run --rm --security-opt label=disable --user "$(id -u):$(id -g)" -e HOME=/tmp \
  -v "$PWD":/app -w /app edmkt-core:dev python -m pytest -q
```

O relatório do import-linter sai sem gravar nada. No `1446a21` ele dá 12 contratos mantidos e
nenhum quebrado, então o contrato quebrado anterior não existe mais, e qualquer violação nova
reprova a suíte.

```bash
docker run --rm --security-opt label=disable --network none -v "$PWD":/app:ro -w /app \
  edmkt-core:dev lint-imports --no-cache
```

Em toda etapa que toca o front, o gate no container `web`.

```bash
docker compose run --rm --no-deps web sh -c "npx tsc -b && npx eslint . && npx prettier --check . && npx vitest run"
```

Nas etapas só de documentos (0, 2 e 12), a conferência de estilo das linhas novas, que procura
travessão, dois-pontos seguido de espaço e linha acima de 100 colunas. Um acerto numa linha de
tabela, de código ou de atributo HTML não conta, e a revisão decide o resto.

```bash
git diff -U0 HEAD -- docs | grep '^+[^+]' | grep -n -e ' — ' -e ': ' -e '^.\{102,\}'
```

Nas etapas 3, 4, 5a, 5b e 6, o `schema.d.ts` sai do OpenAPI gerado sem a api, com o scratchpad em
`$SCRATCH`. O `--no-deps` é obrigatório, porque sem ele o `run` sobe a api pelo `depends_on`.

```bash
docker run --rm --security-opt label=disable --network none -e PYTHONDONTWRITEBYTECODE=1 \
  -e PYTHONPATH=/app/src -v "$PWD":/app:ro -v "$SCRATCH":/out -w /tmp edmkt-core:dev \
  python -c "import json; from api.main import create_app; open('/out/openapi.json','w').write(json.dumps(create_app().openapi(), indent=1))"
docker compose run --rm --no-deps --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$SCRATCH":/out \
  web npx openapi-typescript /out/openapi.json -o src/http/schema.d.ts
```

A tela é conferida sem gravar, pelo roteiro da etapa 1, em 1500px e 1100px, contra a linha de base.
O dev server do `web` serve a árvore de trabalho, então a captura vê a etapa antes do commit. O GET
passa à api real, e todo outro método é bloqueado. Enquanto a api não for recriada, o roteiro
responde a rota da tela e a da origem com o dado real do A439 da turma 6, de um retrato tirado do
`app.db` por consulta só de leitura (`mode=ro`). O de 08/10/2026 está no scratchpad desta sessão,
com as chaves `classroom`, `assignment`, `extracted_at`, `model_id`, `problems`,
`knowledge_components`, `links`, `sampled_solutions`, `evidence` e `candidates`, e numa sessão nova
ele é tirado de novo do mesmo jeito. O retrato não traz execuções, então o `correct_run_count` vem
de outra contagem só de leitura das execuções corretas por problema, que em 08/10/2026 dava entre
365 e 421 nos dez problemas. A origem do A439 da turma 1 sai do mesmo jeito, sem solução
amostrada, candidato nem trecho. Os estados que o banco não tem são simulados, o rascunho com um
problema sem conceito e `correct_run_count` 0, o aprovado, o vínculo do professor, o problema sem
enunciado e o problema sem solução. Os logs da api confirmam zero escritas.

A regressão do KCGen-KT, com o marcador `regression`, não roda, porque o método não muda, e a
suíte padrão já confere a Q-matrix do A439. Nada grava no `app.db` fora da recriação que o Leo
autorizar, e nenhuma etapa usa a GPU nem a cota.

## Execução

- Commits locais no `main`, um por etapa, no padrão do repositório (`docs: ... (etapa 0)`,
  `feat(api): ... (etapa N)`, `feat(web): ... (etapa N)`). A 5 e a 9 têm um commit por parte (5a,
  5b, 9a, 9b e 9c).
- A revisão independente de cada etapa é feita por um subagente que não escreveu o diff, contra
  este plano e as decisões, antes do commit, e as correções entram no mesmo commit. No fim, uma
  revisão independente da tela inteira, com as correções no commit seguinte ao da etapa 12.
- As partes mecânicas vão para subagentes em Sonnet, com a minha revisão. São a saída do mesclar
  (3), a saída da descrição (5b), a regeneração do `schema.d.ts` e o ajuste das fixtures, os
  espécimes da página v6 (2), a aba Problemas (9c) e os documentos do fechamento (12).
- Sem pontos de parada. A api é recriada depois da etapa 6 (W), com a sequência da seção seguinte,
  e as conferências da tela ficam para a validação do Leo no fim. O som só toca se houver problema.
- Entre o primeiro commit do backend e a recriação da api, nada de extração nem de treino (seção
  seguinte).
- O push só sai quando o Leo pedir.

## Depois do plano, com o Leo

**A recriação da api.** Ela entra depois da etapa 6, autorizada pelo Leo. As migrações `0021` e
`0022` só chegam ao `app.db` quando a api sobe de novo, porque o `run_migrations()` roda no lifespan
(`src/api/main.py:31-41`), e o serviço não tem reinício automático (`docker-compose.yml:12-54`).
O Leo decidiu recriá-la depois da etapa 6, antes do front (W). O `web` serve a
árvore de trabalho pelo Vite (`docker-compose.yml:59-83`), então cada etapa do front já vale na
tela aberta, e contra a api antiga a Conceitos perde os campos novos. Recriada, o `npm run types`
volta a servir. A sequência é esta.
1. Nenhum job rodando, porque o restart perde o job.
2. Conferir pela rota da tela, só com GET, que os nomes do A439 da turma 6 continuam os da tradução
   gravada em `tests/data/kc/a439_reference_extraction.json`. Em 08/10/2026 os 25 conferem pelo
   retrato descrito em Verificação. Um renome feito antes da `0021` não deixa rastro e ficaria com
   as estrelas, então até a recriação o Leo não renomeia.
3. Parar a api, que fecha o banco e devolve o WAL ao arquivo principal, e conferir que o
   `app.db-wal` está vazio ou não existe. O `app.db` é do root e em WAL, e com a api parada a cópia
   não pega o banco no meio de uma escrita.

   ```bash
   docker compose stop api
   ls -la app.db*
   ```

4. A cópia de segurança, antes do `DROP COLUMN`, que não se desfaz. Ela fica no scratchpad até o
   Leo confirmar a tela, como na regra dos backups temporários, e só então é apagada. Se o WAL não
   estiver vazio, ele vai junto, com o nome da cópia mais `-wal`, e o SQLite o aplica ao abrir.

   ```bash
   cp app.db "$SCRATCH/app-before-0022.db"
   ```

5. O ensaio das migrações numa segunda cópia, que deve imprimir `22 []`, a versão e o
   `foreign_key_check` vazio. A segunda cópia é apagada depois.

   ```bash
   cp "$SCRATCH/app-before-0022.db" "$SCRATCH/app-rehearsal.db"
   docker run --rm --security-opt label=disable --network none --user "$(id -u):$(id -g)" \
     -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/app/src -v "$PWD":/app:ro \
     -v "$SCRATCH":/out -w /tmp edmkt-core:dev python -c "
   from api.shared.infrastructure.database.sqlite_connection import connect
   from api.shared.infrastructure.database.migrations.runner import run_migrations
   c = connect('/out/app-rehearsal.db'); run_migrations(c)
   print(c.execute('PRAGMA user_version').fetchone()[0], c.execute('PRAGMA foreign_key_check').fetchall())"
   ```

6. Só com o ensaio limpo, `docker compose up -d --force-recreate api`.
7. Conferir, só lendo, que o banco real está na versão 22, pela api e com `mode=ro`, que o
   `npm run types` gera o mesmo `schema.d.ts` (diff vazio) e que a tela mostra o A439 com as
   estrelas.

   ```bash
   docker compose exec api python -c "import sqlite3; c = sqlite3.connect('file:/app/app.db?mode=ro', uri=True); print(c.execute('PRAGMA user_version').fetchone()[0])"
   ```

O `DROP COLUMN` apaga os 20 textos de descrição das turmas 3 e 5, como o Leo decidiu. Até a
recriação, os workers, que são subprocessos da api, importam o código novo da árvore
(`docker-compose.yml:30`) contra um banco ainda na versão 20. Hoje nenhum caminho de worker lê o
`kc` pelo repositório, e o da extração só insere (`run_kc_generation_use_case.py:96`), mas a regra
de não extrair nem treinar nesse intervalo evita conferir caminho por caminho.

**O A439 da turma 6, antes de apagar a turma 1.** A turma 1 (CSEDM Spring 2019) tem o único
exercício treinado do banco, o A439 antigo, que serve para conferir a tela Análise, a próxima. A
ordem segura é esta.
1. O Leo revisa e aprova os conceitos do A439 da turma 6 na tela nova. Os 10 problemas têm
   conceito, então o Aprovar habilita.
2. O Leo treina o A439 da turma 6 pela tela, na GPU, em alguns minutos. O treino pela tela já foi
   testado pelo Leo em 08/10/2026, na turma 7 "Teste novo", e este treino congela os conceitos
   do A439.
3. Só então o Leo apaga a turma 1 e a turma 5 pela tela Turmas, com soft delete.

Apagar a turma 1 antes do treino deixa o app sem exercício treinado até lá, o que o Leo pode
aceitar.

**A nova extração.** O Leo faz pela aplicação, porque gasta cota. Os conceitos novos nascem com o
`generated_name` e mostram as estrelas.

**O push**, quando o Leo pedir.

## Estado

| Etapa | Situação |
|---|---|
| 0 | Concluída, commit `311dfbb` |
| 1 | Concluída, sem commit. O balão do `InfoHint` e do `GeneratedByML` nasce por baixo do diálogo do aluno, filho do `body` e encoberto pelo `<dialog>` modal |
| 2 | Concluída, commit `e574571` |
| 3 | Concluída, commit `04c8824` |
| 4 | Concluída, commit `6d31cc7` |
| 5a | Concluída, commit `83af401` |
| 5b | Concluída, commit `23f3130` |
| 6 | Concluída, commit `b37cb13` |
| Recriação da api | Concluída em 08/10/2026, a pedido do Leo, depois da etapa 6, com a cópia de segurança e o ensaio das migrações (banco na versão 22) |
| 7 | Concluída, commit `77b7635` |
| 8 | Concluída, commit `e210085` |
| 9a | Concluída, commit `b4e7e79` |
| 9b | Concluída, commit `49dadd7` |
| 9c | Concluída, commit `4ad1127` |
| 10 | Concluída, commit `f502404` |
| 11 | Concluída, commit `78401d0` |
| 12 | Concluída, no commit desta etapa |
| Revisão independente da tela | A fazer |
