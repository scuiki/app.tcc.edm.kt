# Plano da base do front v5

Leva o `src/web` à linguagem v5 nas peças que sobrevivem às telas, que são o F1 (tokens e
fundamentos), a migração dos componentes que já existem e o F3 (tabelas). As telas continuam com a
organização antiga até serem refeitas uma a uma (Conceitos, Análise, Turma, Importar dados, Turmas).
Aprovado pelo Leo em 08/10/2026. O porquê das decisões está no `DECISIONS.md`, na seção
Frontend, e este documento diz como e em que ordem elas entram no código.

## Escopo

Entram os tokens, as fontes, as regras globais, os controles de `components/ui`, a etiqueta de
situação com ícone, os estados, os estágios, a mensagem de resultado, o caminho e o cabeçalho com a
etiqueta ao lado do título, o menu com os pontos de situação e os ícones, a tabela comum nas tabelas
da Análise e de Turmas, o histograma, a barra e o marcador `GeneratedByML`.

Ficam de fora, cada um com a tela que o usa.
- Conceitos. A linha de fatos, as ações na faixa das abas, o diálogo largo, `GeneratedByLLM`, o bloco
  de código, a matriz e a saída do PageActionBar (ApprovalBar).
- Análise. O triângulo e a lista da recorrência, o ConceptChips e a linha expandida da aba Problemas,
  os blocos do diálogo do aluno e a curva de perda além da troca do token (F4).
- Turma e Turmas. A coluna Exercícios da tabela de Turmas (pede backend) e a atividade recente (B7).
- Importar dados. A área de soltar vertical, o indicador de passos, o arquivo enviado, a tabela do
  resultado (muda com o B4), o título de cartão com ícones, o rodapé com ações, o sucesso com
  circle-check e a saída do PageActionBar.
- Depois da Conceitos, numa etapa própria. O menu que recolhe abaixo de 900px.

## Decisões fechadas com o Leo

- A. O menu que recolhe abaixo de 900px fica fora da base.
- B. Alinhamento pelo HTML, mais recente que a regra da v1 no DESIGN.md. Em todas as tabelas, nome à
  esquerda, números e etiquetas centralizados sob rótulos centralizados, botões à direita. Critério
  geral, entre o DESIGN.md e o HTML vale o atualizado por último.
- C. O menu mantém os ícones de tela, e Importar dados continua nele.
- D. Pontos de situação. ready_for_kc_generation e kc_draft com o ponto vazio e a dica "Aguardando
  conceitos", kc_approved meio preenchido, trained azul e statistics_only sem ponto.
- E. "Modelo treinado" vira "Treinado" na etiqueta, já na base.
- F. O `--radius` sai, e o raio vai a 0 no reset global, com exceção só dos pontos e marcadores.
- G. O marcador do Code-DKT diz "Dado estimado por aprendizado de máquina".
- H. O roteiro de captura pelo CDP fica no scratchpad, fora do repo.
- I. A tabela de Turmas entra na base.

## Padrões adotados

- O branco sobre preenchido ganha o token `--color-text-inverse`, usado no botão, nos passos e no
  balão, no lugar dos `#ffffff` literais e do `--color-surface` do balão.
- Foco com 2px de folga em todo controle, como o DESIGN.md (o espécime do campo usa 0).
- Uma regra global `accent-color: var(--color-text)` deixa os rádios e caixas de marcar sem azul.
- O link global ganha a cor do texto e o sublinhado de 1px, e o `a:hover` só engrossa o sublinhado,
  para não sublinhar os itens do menu.
- Ícones. Conceitos é `Blocks` em todo lugar (menu, aba e linha expandida), a aba Problemas é
  `FileCode`, e Importar dados no menu é `Upload`, o mesmo do futuro botão da Turma. Todo ícone volta
  ao traço de 2px nas peças da base.
- A etiqueta de situação recebe só um `LucideIcon`. O mapa situação para ícone mora em
  `features/assignments/api`, ao lado do `ASSIGNMENT_STATUS_LABEL`, por ser o único lugar que as
  funcionalidades e o `app/` podem importar. O mapa dos pontos fica no SideMenu, o único que o usa.
- O `GeneratedByML` é componente de produto e vai para `components/` (ao lado do PageHeader), com o
  texto dentro dele. O `ESTIMATED_HINT` sai, e a frase longa do domínio (`MASTERY_HINT`) fica no
  dashboard.
- A tabela comum é a `DataTable` em `components/ui`, com o `ColumnHeader` (cabeçalho simples) e o
  `SortableHeader` com a mesma estrutura. Não tem variante (o alinhamento é um só) nem largura mínima,
  que fica com quem precisa (900px na Análise, nenhuma em Turmas).
- O diálogo mantém o ! vermelho no tom danger (é alertdialog) e a largura de 440px.
- O asterisco do campo obrigatório fica, em `--color-text-muted`.
- O corpo do cartão segue sem espaçamento próprio, e o invólucro da tabela traz o seu (14px 16px).
- A mensagem de resultado no tom neutro fica sem ícone (o circle-alert é só vermelho).
- O respiro da área principal fica como está até o PageActionBar sair.
- O favicon vira o capelo em `#161616`, sem raio. `color-scheme: light` no tokens.css. Sem `.t-body`
  e sem carregar o Arimo.
- `.mono` vira `.num` só em número e identificador. As duas mensagens de erro técnico ficam sem
  classe, na fonte da interface.
- O F1 sai em dois commits, primeiro cores e forma, depois a tipografia. O vite build não entra no
  gate.

## Etapas

Cada etapa é um commit, com uma revisão independente do diff contra o plano antes de commitar. Em
toda etapa, o comentário que a etapa torna falso é corrigido em qualquer arquivo de `src/web/src`,
não só nas linhas tocadas, pela busca dos termos que ela muda (azul, arredond, mono, Arial, "!",
eixo, aside).

### 0. Registro e nomes, antes do código
- Este plano vira `docs/FRONTEND_BASE_PLAN.md`, com a tabela de Estado por etapa, e a seção 9 do
  `IMPLEMENTATION_PLAN.md` aponta para ele.
- `GLOSSARY.md`. Entram a tabela de dados (`DataTable`, com `ColumnHeader` e `SortableHeader`), a
  etiqueta de situação (`ASSIGNMENT_STATUS_LABEL` e `ASSIGNMENT_STATUS_ICON`) e o ponto de situação
  (três modificadores, "Aguardando conceitos", statistics_only sem ponto) na seção Estados do
  assignment. O `GeneratedByML` ganha o texto novo, e a entrada domínio troca `EstimatedMark` por
  `GeneratedByML`.
- `DECISIONS.md`, seção Frontend. Raio 0 sem token, alinhamento e o critério do atualizado por último
  (com o menu com ícones como exceção consciente), `--color-text-inverse`, a `DataTable` comum, os
  pontos de situação, "Treinado", o texto do marcador, o `GeneratedByML` subindo antes da segunda
  funcionalidade, o mapa de ícones no `api/`, os ícones Blocks, FileCode e Upload e o menu recolhível
  adiado.
- `DESIGN.md`. A regra de alinhamento, o `--radius` fora da tabela Forma, o `--color-text-inverse` na
  tabela Cor e no balão, o texto do marcador, os ícones do menu (ícones de tela e o ponto, sem os de
  etapa), o `upload` também no menu, statistics_only sem ponto, os estágios em azul nos dois
  diálogos, e uma linha de revisão da v5 em 08/10 na tabela de Versões, sem renomear o HTML.
  `design-system-v5.html`, o texto do marcador.

### 1. Linha de base visual, sem commit
- Script Node sem dependências (WebSocket nativo do Node 22 do host) no scratchpad, com o Chrome do
  flatpak sem janela e o domínio Fetch. O GET passa à api real, todo método diferente de GET é
  bloqueado e as fontes do Google passam. Estados que o banco não tem (job rodando, rascunho) são
  simulados.
- Captura Turmas, Turma, Importar dados, Conceitos (rascunho e treinado), Análise (três abas), os
  diálogos (aluno, treino, extração, exclusão, renomear), o estado vazio e a Página não encontrada,
  em 1500px e 1100px. Os logs da api confirmam zero escritas.

### 2. F1, cores e forma
- `tokens.css` com os valores da v5. Entram `--color-active`, `--color-primary` e `-hover`,
  `--color-focus`, `--color-model` e `-strong`, `-soft`, `-soft-border`, `--color-observed`,
  `--color-text-inverse` e `--table-row-height`. Saem `--color-accent*`, `--color-bar-observed` e
  `-predicted`, `--color-surface-icon`, `--color-menu-rule` e o `--radius` (as 33 declarações saem,
  o reset zera o raio, pontos e marcadores mantêm 50%). `color-scheme: light`, a regra do link, o
  foco e o `accent-color` global.
- Os 41 usos do azul de ação e os demais tokens que saem remapeados conforme o mapa. O ponto
  kc_approved já ganha o meio preenchido da v5, para não ficar igual ao de treinado. O LossChart lê
  `--color-model` sem os hex de reserva. O ImportSteps separa o passo feito do atual. Os usos sem
  desenho na v5 vão a neutros, e os raios literais vão a 0. Favicon.
- Saem os `text-decoration: none` que escondem links (cartão de exercício da Turma, nome na tabela
  de Turmas, caminho), para a regra global do link valer.
- As frases de Estado do `DESIGN.md` e do `IMPLEMENTATION_PLAN.md` e o "A migração troca…" das cores
  passam a dizer o que já mudou.
- Teste novo `src/web/tokens.test.ts`, ao lado do `architecture.test.ts` e no include do
  `tsconfig.node.json`, lendo os arquivos com `node:fs`. Confere que todo `var(--x)` e todo
  `tokenColor('--x')` usado em `src/web/src` está declarado no `tokens.css`, e que não há cor hex ou
  rgb fora dele, exceto nos testes.
- Verificação extra. O grep dos nomes antigos sai vazio, e a captura mostra o primário preto e
  nenhum texto ou borda sumindo.

### 3. F1, tipografia
- `index.html` com Public Sans 400, 600 e 700. `--font-sans`, `--font-data` e `--font-code`, e saem
  `--font-mono` e `--font-table`. `.mono` vira `.num` nos números e identificadores, e as duas
  mensagens de erro ficam sem classe. `AnalysisTable.css` usa `--font-data`. O "A migração troca…"
  da tipografia no `DESIGN.md` é atualizado.
- Ponto de conferência com o Leo. Depois desta etapa mando as capturas de antes e depois e sigo com
  a aprovação dele.

### 4. Controles
- Button com fonte Public Sans explícita, svg que não encolhe, `.icon-btn:disabled` e traço padrão.
- Campo com o rótulo em `--color-text-body`, padding 0 10px, fontes e o asterisco neutro. Busca com
  240px, a borda no invólucro e o anel por `:focus-within`.
- Abas com a faixa branca e a fonte. Diálogo com os paddings da v5. Dica com `CircleQuestionMark`.
  O balão é conferido. Nenhum teste muda.

### 5. Etiqueta com ícone, tom de modelo e "Treinado"
- Badge com o tom `model` no lugar de `accent`, a prop `icon`, gap de 6px, o ícone de 13px com
  margem de -2px e fonte explícita. `ASSIGNMENT_STATUS_ICON` com Blocks nas três situações de
  conceitos, Brain em trained e nada em statistics_only. Uma função ao lado dos mapas devolve tom,
  ícone e rótulo, no lugar das três cópias nas páginas.
- "Treinado" só em `useAssignments.ts` e `ClassroomStatusBadge.tsx`, que também passa o Brain no
  trained. O título do diálogo de treino, a frase do editor e a da exclusão ficam como estão.
- Os testes ajustados são o ClassroomsPage.test, o ClassroomPage.test, o MasteryDashboardPage.test e
  o SideMenu.test.

### 6. Estados, estágios, mensagem e caminho
- `state--loading` em linha. O estado vazio centralizado, com gap de 6px, padding de 18px, a frase
  em 12px muted e o ícone num quadrado `--color-hover`. StageList com margem 0. Mensagem de resultado
  com ícone só no danger (TSX). Caminho com 13px, gap de 6px, `--color-text-secondary`, links e item
  atual em 400 e o separador muted.
- Teste novo no OutcomeMessage.test, o neutro sem svg e o danger com.

### 7. Menu e ícones
- Pontos pela decisão D, com o CSS da v5, a dica "Aguardando conceitos" no vazio e nada em
  statistics_only. Layers vira Blocks (menu, aba Conceitos e linha expandida da ProblemsTable),
  ClipboardList vira FileCode na aba Problemas e Database vira Upload. Sai o traço 3 no hover do
  sinal.
- SideMenu.test ganha kc_draft e statistics_only nas fixtures e confere as dicas dos pontos e a
  ausência de ponto. O grep de `Layers`, `ClipboardList` e `Database` sai vazio.

### 8. Caminho e cabeçalho
- O Breadcrumb perde a prop `aside`, o item sem link que não é o último vira texto simples e o
  `aria-current` fica só no último. O PageHeader ganha a prop `badge`, fora do h1 e a 12px dele, e
  perde a prop `icon` (um uso). A `description` fica até cada tela. A Análise e a Conceitos passam a
  etiqueta ao PageHeader.
- Os testes ajustados são o Breadcrumb.test, o KnowledgeComponentsPage.test e o
  MasteryDashboardPage.test. Entram testes para a etiqueta no PageHeader com o h1 intacto, o item do meio sem `aria-current` e a
  etiqueta fora da nav.

### 9. F3, a tabela comum (Análise e Turmas)
- `DataTable.tsx` e `.css`. Invólucro com rolagem lateral e padding 14px 16px. Tabela em
  `--font-data`, corpo em 13,5px, th em 12,5px, 600, `--color-text-body`, padding 0 8px, line-height
  1.25 e nowrap, td com padding 4px 8px, th e td com 32px, primeira coluna à esquerda com 4px, traço
  `--color-text` sob o cabeçalho e no fim, fio `--color-rule` entre as linhas, hover
  `--color-surface-subtle`, sem fio vertical. Classes de célula para nome (700, nowrap), número e
  etiqueta (centralizados, nowrap, tabular-nums), apoio, sem valor e botões (à direita, 4px).
- `ColumnHeader` e `SortableHeader` com a prop `leading` para o marcador fora do botão, o rótulo
  truncado em 150px com o texto inteiro no Tooltip, chevron de 14px e a seta ativa em `--color-text`.
  O alinhamento padrão vira center, e os quatro `'start'` das colunas de barra saem.
- ConceptsTable, ProblemsTable, StudentsTable e ClassroomTable passam à DataTable. Na de Turmas,
  Problemas, Alunos, Criada em e Situação usam a classe de número. Saem a quebra do rótulo e o
  modificador `--ruled`. A Análise mantém 900px de largura mínima. A recorrência fica centralizada,
  com o sublinhado de 3px.
- Entram testes da DataTable no ui.test e do SortableHeader com o marcador fora do botão e o Tooltip
  no viz.test. A captura em 1500px confere que a tabela de Turmas não rola de lado.

### 10. F3, histograma, barra e GeneratedByML
- Histograma sem eixo (a prop `axis` sai, com os dois consumidores), faixa vazia `.is-zero` sem
  altura inline, 20px, gap de 2px, sem o mínimo de 2% e a dica "{a} a {b}%, {n} alunos". RatioBar
  com a largura mínima no componente.
- `components/GeneratedByML.tsx` com "Dado estimado por aprendizado de máquina". Sai o
  `ESTIMATED_HINT`, a regra do rodapé da Análise acompanha a classe e o `title` nativo do diálogo do
  aluno vira Tooltip.
- Mudam o viz.test (a dica nova e a faixa vazia) e o MasteryDashboardPage.test (o nome do
  marcador), e o GeneratedByML ganha um caso próprio.

### 11. Fechamento nos documentos
- `ARCHITECTURE.md` (comentário de CSS com `/* */`, o `api/` com os rótulos e ícones de situação, a
  DataTable e o GeneratedByML). `IMPLEMENTATION_PLAN.md` (seções 2, 4 e 9, e a linha dos
  comentários). A linha de comentários do `CLAUDE.md`, que passa a citar o `/* */` do CSS. O Estado
  deste plano e a memória.

## Verificação

Em toda etapa, o gate web no container
(`docker compose run --rm --no-deps web sh -c "npx tsc -b && npx eslint . && npx prettier --check . && npx vitest run"`),
o `code_comments_test` na edmkt-core, a captura em 1500px e 1100px contra a linha de base e a revisão
independente do diff. Nada grava no `app.db`, e nenhuma etapa usa a GPU nem a cota.

## Execução

Commits locais no main, um por etapa, e o push no fim, depois da revisão do Leo. As partes mecânicas
vão para subagentes em Sonnet, com a minha revisão. O ponto de conferência é depois da etapa 3, e o
som só toca se houver problema.

## Estado

| Etapa | Situação |
|---|---|
| 0 | Concluída, commit `7c4fb56` |
| 1 | Concluída, sem commit |
| 2 | Concluída, commit `736bfb0` |
| 3 | Concluída, commit `3f1eea1`, conferida pelo Leo |
| 4 | Concluída, commit `1a83ebf` |
| 5 | Concluída, commit `cfd03d0` |
| 6 | Concluída, commit `94b2a85` |
| 7 | Concluída |
| 8 | Pendente |
| 9 | Pendente |
| 10 | Pendente |
| 11 | Pendente |
