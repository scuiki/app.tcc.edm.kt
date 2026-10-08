# Design

As regras visuais do app docente. O porquê de cada decisão fica em `DECISIONS.md`, na seção
Frontend. Os valores (hex, sombras, medidas) ficam no `src/web/src/styles/tokens.css`, e aqui cada
papel é citado pelo nome do token.

**Versão 5, 30/09/2026, revista em 08/10/2026.** Referência visual em [`design/design-system-v5.html`](design/design-system-v5.html),
que abre direto no navegador.

**Estado.** Este documento é a especificação. A migração para ela segue o `FRONTEND_BASE_PLAN.md`.
As cores, as sombras, o raio e a tipografia do `tokens.css` já são os da v5, e os componentes
ainda seguem a linguagem anterior. As cinco telas ainda têm a
organização antiga e mudam uma a uma depois da base.

## Princípios

- **Entregar o dado, não a interpretação.** Sem níveis, faixas ou cores de alerta sobre um número.
  O professor ordena e lê.
- **Azul significa modelo.** O azul só aparece quando um modelo produziu o que está na tela, e o
  ícone diz qual. O cérebro é o Code-DKT e as estrelas são o modelo de linguagem. Botão, link, foco,
  menu e abas não são azuis.
- **Três papéis de cor.** Cinza para a interface, azul para o modelo, vermelho para erro e
  exclusão. Não há verde nem âmbar.
- **Sombra marca objeto.** Só o cartão, o diálogo e a barra superior têm sombra. Nada dentro deles.
- **Raio 0.** Botões, campos, cartões, etiquetas, barras e histogramas têm canto vivo. Só os pontos
  de situação e os marcadores de modelo são redondos.
- **Duas fontes, dois papéis.** Public Sans na interface. Arial nos dados técnicos (tabela, gráfico
  e número), o mesmo da monografia.
- **Texto em português.** "Dados", nunca "dataset". O código continua em inglês.

## Cor

Nenhuma cor é escrita no ponto de uso. Todo componente lê um token, e todo token tem uma situação
de uso.

| Papel | Token | Onde |
|---|---|---|
| Interface | `--color-page` | Fundo da página |
| | `--color-surface` | Cartão, menu, barra superior |
| | `--color-surface-subtle` | Hover de linha de tabela, rodapé de diálogo |
| | `--color-hover` | Hover de controle |
| | `--color-active` | Item ativo do menu |
| | `--color-rule` | Fio dentro do cartão e entre linhas de tabela |
| | `--color-control-border` | Contorno de campo, botão secundário e botão de ícone |
| Texto e ação | `--color-text` | Texto, traço do cabeçalho de tabela, balão |
| | `--color-text-body` | Texto corrido |
| | `--color-text-secondary` | Menu, aba inativa |
| | `--color-text-muted` | Apoio, eixo de gráfico, ícone de dica |
| | `--color-text-disabled` | Desabilitado |
| | `--color-primary` e `--color-primary-hover` | Botão primário |
| | `--color-focus` | Anel de foco |
| | `--color-text-inverse` | Texto sobre o preenchido, no botão primário e no destrutivo, no passo atual e no balão |
| Modelo | `--color-model` | Domínio, distribuição, curva de perda, ponto de treinado, estágios da extração e do treino |
| | `--color-model-strong` | Hover das marcas do modelo, texto sobre o azul claro |
| | `--color-model-soft` e `--color-model-soft-border` | Etiqueta Treinado, fundo dos marcadores de modelo |
| Observado | `--color-observed` | Taxa de acerto e toda barra do que aconteceu |
| | `--color-bar-track` | Trilho das barras |
| Erro | `--color-danger` | Ícone de erro, contorno de campo com erro, botão destrutivo |
| | `--color-danger-text` | Texto de erro, hover do destrutivo |

## Tipografia

Duas fontes com papéis fixos. A fronteira entre elas é nítida, para a troca parecer escolha e não
acaso.

| Token | Fonte | Onde |
|---|---|---|
| `--font-sans` | Public Sans (400, 600, 700) | Títulos, menu, abas, botões, campos, etiquetas (mesmo com número, como "10 problemas"), balões e texto corrido |
| `--font-data` | Arial, com `Liberation Sans` e `Arimo` como reserva | A tabela inteira, cabeçalho incluído. O gráfico inteiro, título e fonte da figura incluídos. Todo número fora deles (contagem, percentual, data, versão, identificador), pela classe `.num` |

O Arial é o mesmo da monografia, então tabelas e figuras entram no texto do TCC sem destoar. No
Linux a reserva é a Liberation Sans, que tem as mesmas medidas do Arial, e o layout não muda entre
máquinas. Os algarismos do Arial já têm largura fixa, e `.num` mantém `tabular-nums` mesmo assim.
A única exceção é `--font-code`, uma fonte mono do sistema, só em bloco de código, porque o
alinhamento e a indentação do código dependem da largura fixa.

| Nível | Classe | Tamanho e peso |
|---|---|---|
| Título da página | `.t-page-title` | 22px, 600 |
| Título de seção | `.t-section-title` | 16px, 600 |
| Corpo | (padrão do `body`) | 13px, 400 |
| Apoio | `.t-support` | 12px, 400, `--color-text-muted` |

A tabela usa 13,5px no corpo e 12,5px no cabeçalho. O título de cartão usa 13px em 600.

## Forma e espaço

| Medida | Valor | Onde |
|---|---|---|
| Raio | 0 | Tudo, exceto pontos de situação e marcadores de modelo. É regra do reset global, sem token |
| `--control-height` | 36px | Botão, campo, aba |
| `--control-height-compact` | 32px | Botão de ícone |
| Botão compacto | 28px | Ação secundária dentro de cartão |
| `--table-row-height` | 32px | Linha e cabeçalho de tabela |
| Cabeçalho de cartão | 48px | Todo cartão com título |
| Linha do menu | 38px | Menu lateral |
| Barra superior | 56px | Uma por app |
| Etiqueta | 22px | Situação e contagem |

Três sombras, cada uma com um só lugar. `--shadow-card` no cartão e na figura, `--shadow-dialog`
no diálogo e `--shadow-bar` na barra superior.

## Componentes

Cada variante existe porque tem uma situação de uso. Uma variante sem uso não nasce.

**Botões.** O primário é preto, e há um por tela ou diálogo. O secundário é branco com contorno, a
alternativa neutra ao lado do primário. O destrutivo é vermelho preenchido e só aparece no diálogo
que confirma uma exclusão. O botão de ícone (32px, com contorno) é a ação de linha em tabela. O
compacto (28px) é a ação secundária dentro de um cartão.

**Foco e link.** O foco é um anel de 2px em `--color-focus` com 2px de folga, nunca removido sem
substituto. O link é sublinhado na cor do texto e engrossa no hover.

**Campo.** Caixa inteira com `--color-control-border`, como o botão secundário. No erro, o contorno
fica vermelho e a mensagem aparece abaixo, em `--color-danger-text`.

**Etiqueta.** Retangular, de 22px. A neutra é cinza. A de modelo (Treinado) usa o azul claro, e é
a única etiqueta com cor. A etiqueta de situação leva o ícone da etapa, os blocos nas etapas de
conceitos (pronto, rascunho e aprovados) e o cérebro no Treinado. As demais situações ficam sem
ícone.

**Barra superior.** Branca, com `--shadow-bar`, só com o ícone do capelo em `--color-text`, sem
texto ao lado.

**Menu lateral.** Árvore com turma, exercício e tela, cada nível recuado. O item ativo tem
fundo `--color-active` e negrito, sem barra lateral. O ponto de situação do exercício fica vazio
quando aguarda conceitos, com a dica "Aguardando conceitos", meio preenchido com os conceitos
aprovados e em `--color-model` quando existe um modelo treinado. O exercício que só tem estatísticas
fica sem ponto, porque não chega a treinar. Cada item de tela leva o ícone da sua tela.

**Abas.** A aba ativa tem texto `--color-text` em 600 e traço de 2px na mesma cor. A faixa das abas
é branca, igual ao cartão.

**Cartão.** Branco, com `--shadow-card` e sem borda, com cabeçalho próprio de 48px e fio abaixo
dele. O rodapé opcional tem 44px e texto de apoio.

**Diálogo.** O `<dialog>` nativo, com `--shadow-dialog` sobre o fundo escurecido. O rodapé é
`--color-surface-subtle`, com as ações à direita e a principal por último.

**Área de soltar arquivo.** Contorno tracejado em `--color-control-border`. Com o arquivo por cima,
o contorno fica sólido em `--color-text` e o fundo `--color-hover`. Importar dados vem antes de
qualquer modelo, então a área não tem azul.

**Caixa do pacote.** A área de soltar do pacote é horizontal, com o ícone à esquerda e as duas
linhas à direita. Depois do envio, a mesma caixa mostra o arquivo com a pasta (`folder`), o tamanho,
o Trocar e uma linha de estado, e na recusa essa linha é o erro em duas linhas. A caixa tem 104px
nos três estados, para a tela não pular entre os passos.

**Lista de requisitos.** Cada linha é um `PackageRequirement`, com uma marca quadrada de 20px à
esquerda, vazia antes do envio, preenchida em `--color-text` com o visto quando atendido e em
`--color-danger` com o xis quando falta. O texto de apoio diz o que se espera e, depois do envio, o
arquivo que atendeu.

**Indicador de passos.** Os passos numerados em linha, ligados por um fio. O atual é preenchido em
`--color-text`, o feito leva o visto com contorno `--color-text` e o que falta fica com contorno
`--color-control-border`.

**Título de cartão com ícone.** Quando o cartão reúne coisas que o app já representa por ícone, os
ícones ficam juntos antes do texto do título, em `--color-text-secondary`, e não se repetem nos
rótulos dos campos, como em "Turma e arquivo" com as pessoas e a pasta.

**Rodapé com as ações do formulário.** As ações de um formulário ficam no rodapé do cartão, com o
fio acima, a frase de apoio à esquerda e os botões à direita, o primário por último. O app não tem
barra fixa presa à janela.

**O que o sistema ajustou.** Os avisos de uma importação que não a impedem, como compilações
repetidas descartadas, numa lista neutra de título e detalhe, sem ícone de alerta. O ! vermelho fica
para a recusa, que não grava nada.

**Lista de estágios.** Em `--color-model`, tanto na extração de conceitos, feita pelo modelo de
linguagem, quanto no treino do Code-DKT, porque os dois são trabalho de modelo. A extração tem cinco
estágios, "Identificando os conceitos de cada problema", "Agrupando os conceitos parecidos e
nomeando cada grupo", "Ligando os conceitos aos problemas", "Apontando onde cada conceito aparece
nas soluções" e "Traduzindo os conceitos para o português".

**Carregamento e vazio.** O indicador de carregamento (spinner) é `--color-text`. O estado vazio
tem o ícone num quadrado `--color-hover`, um título e uma frase de apoio.

**Mensagem de resultado.** O erro tem ícone `--color-danger` e título `--color-danger-text`. O
sucesso é neutro, com o ícone em `--color-text`.

**Marcadores de modelo.** Um ícone em `--color-model-strong` sobre um círculo `--color-model-soft`
de 18px, com a dica de onde o dado veio.
- `GeneratedByML`, o cérebro, "Dado estimado por aprendizado de máquina", para o que o Code-DKT produziu. Fica antes do
  rótulo de toda coluna que vem do modelo.
- `GeneratedByLLM`, as estrelas, "Gerado pelo modelo de linguagem", para o que o LLM escreveu, como
  o nome do conceito e a descrição do problema. Fica no fim do texto (20px, e 24px num título) ou
  antes do rótulo de coluna. Some do nome do conceito quando o professor o renomeia, porque o nome
  passa a ser dele.

**Dica, alerta e balão.** A dica é o ícone de ? (`circle-question-mark`) em `--color-text-muted`. O
ícone de ! (`circle-alert`) fica só para alerta e erro, em `--color-danger`, como um problema sem
conceito. O balão é `--color-text` com texto em `--color-text-inverse`, sem raio, e aparece no hover ou no foco pelo
`Tooltip`, nunca pelo `title` nativo.

**Bloco de código.** Em `--font-code`, sobre `--color-surface-subtle`, com a numeração de linha à
esquerda em `--color-text-disabled`. Quando há mais de um arquivo, abas presas ao topo do bloco
trocam o código, e a aba ativa tem o traço de 2px em `--color-text`.

**Matriz de conceitos.** A célula é um quadrado de 20px, preenchido em `--color-text` quando o
conceito está ligado ao problema, que liga e desliga no clique. No exercício treinado a célula fica
em `--color-observed` e não responde. As ações da linha do conceito são lupa, lápis e lixeira, nessa
ordem. Mesclar não existe, porque um conceito duplicado é removido e o outro fica.

**Origem do conceito.** Um diálogo aberto pela lupa, com o nome do conceito e o marcador de gerado,
a linha de fatos, os problemas em que ele aparece em abas e, para cada um, a descrição e as até cinco
soluções corretas que o modelo de linguagem leu, num bloco de código com abas. A tentativa em que
cada aluno acertou fica na dica da aba.

**Cabeçalho ordenável.** A seta da ordenação ativa é `--color-text`, e o rótulo ordenado também.

**Botão de próximo passo.** O secundário compacto, na última coluna da tabela de exercícios, com o
ícone da tela para onde leva. Um por linha, escolhido pela situação: "Extrair conceitos" e "Revisar
conceitos" com os blocos, "Treinar modelo" com o play e "Ver análise" com o gráfico de colunas.

**Busca.** Um campo de 32px com a lupa, na faixa das abas à direita, só na aba que ele filtra, ou no
cabeçalho do cartão quando não há abas.

**Paginação.** Dez linhas por página. À esquerda a contagem ("1 a 10 de 413 alunos"), à direita o
anterior, a primeira e a última página, a atual e as vizinhas, com reticências no meio, e o próximo.
A página atual tem contorno `--color-text`.

**Atividade recente.** Uma lista dos eventos que o professor provocou, do mais novo para o mais
antigo, cada um com o ícone do que mudou, o que foi, onde e a data. Os eventos são turma criada,
dados importados, conceitos extraídos e modelo treinado.

## Ícones

Os ícones vêm do lucide, com traço de 2px. Cada ícone representa uma coisa só, e a mesma coisa leva
o mesmo ícone em todo lugar. O menu leva o ícone de cada tela, e o exercício leva o ponto de
situação no lugar do ícone de etapa, para a lista longa ficar discreta.

| Ícone (lucide) | Representa | Onde |
|---|---|---|
| `blocks` | Conceitos | Menu, aba, botões e etiquetas das etapas de conceitos |
| `file-code` | Problemas | Aba Problemas da Análise |
| `brain` | O Code-DKT | Marcador `GeneratedByML`, etiqueta Treinado, evento de treino |
| `sparkles` | O modelo de linguagem | Marcador `GeneratedByLLM`, no nome do conceito e na descrição do problema |
| `chart-column` | Análise | Menu e botão "Ver análise" |
| `clipboard-pen` | Exercício | Menu e aba Exercícios |
| `users` | Turmas e alunos | Menu, aba Alunos, evento de turma criada |
| `upload` | Importar dados | Menu e botão do cabeçalho da turma |
| `file-check` | Solução correta | Abas das soluções na origem do conceito |
| `search` | Inspecionar | Lupa da linha do conceito, campo de busca |
| `circle-question-mark` | Dica | Todo ícone de dica |
| `circle-alert` | Alerta | Só em vermelho, em alerta e erro |
| `list-checks` | Requisitos | Título do cartão "O que o pacote precisa ter" |
| `folder` | Pacote e arquivo | Título do cartão "Turma e arquivo", arquivo enviado |

## Tabelas

- A tabela inteira usa `--font-data`.
- Sem fio vertical. Traço `--color-text` sob o cabeçalho e no fim da tabela, fio `--color-rule`
  entre as linhas, em todas as tabelas.
- Linha e cabeçalho com a mesma altura, 32px. Um rótulo longo trunca com reticências e mostra o
  texto inteiro no hover, e em tela larga aparece inteiro.
- O histograma da tabela não tem eixo. A escala fica na dica do cabeçalho, e a faixa sem aluno é um
  traço de 1px em `--color-control-border`.
- Em todas as tabelas, o nome fica à esquerda, os números e as etiquetas ficam centralizados sob
  rótulos centralizados e só a coluna de botões fica à direita.
- A taxa de acerto usa a barra em `--color-observed`. Domínio e distribuição usam `--color-model`
  e levam o marcador `GeneratedByML` no rótulo.
- As barras e os histogramas das tabelas são CSS, com canto vivo.

## Gráficos

- Uma figura só entra quando mostra um dado que a tabela não tem. Redesenhar os números da tabela
  em outra forma não é motivo para uma figura.
- A figura inteira usa `--font-data`, para entrar na monografia como está.
- Cada figura tem título, subtítulo com a unidade e a fonte do dado (por exemplo, "Fonte: Code-DKT"
  seguida da versão do modelo).
- As barras são quadradas e o eixo delas começa em zero. A linha não precisa começar em zero.
- Observado e previsto nunca dividem a mesma régua.
- Dois eixos só quando a segunda série é contexto da primeira. Ela fica atrás e apagada, cada eixo
  leva a cor e o título da sua série, e a legenda diz qual eixo é de qual.
- Grade em `--color-rule`, eixo em `--color-text`, rótulos em `--color-text-muted` e o valor
  destacado em `--color-text`.
- Toda marca mostra o valor no hover. A curva de perda marca o último valor.
- O Chart.js desenha as curvas, a de perda e a de aprendizagem. Barras e histogramas das tabelas
  são CSS.

**Curva de aprendizagem.** A taxa de erro em cada oportunidade de praticar um conceito, em
`--color-observed`, com os alunos que chegaram a cada oportunidade em barras atrás, em
`--color-text-disabled` a 35%. A taxa de erro fica no eixo da esquerda, de 0 a 100%, e os alunos no
da direita. A oportunidade é cada execução do aluno num problema que exige o conceito. A curva para
quando menos de 10% da turma chega à oportunidade. Um conceito por vez, escolhido num seletor, com a
linha de fatos da 1ª, da 5ª, da 10ª e da última oportunidade mostrada.

**Execuções por dia.** As execuções da turma em barras de `--color-observed`, com a janela de cada
exercício rotulada acima pelo número dele. Por dia até cerca de 120 dias de disciplina, e por semana
acima disso. Quando exercícios se sobrepõem no tempo, os rótulos empilham em até três faixas, e acima
disso somem, porque o período está na tabela. O eixo vai só da primeira à última janela de exercício,
e o que cair fora é contado numa nota. O dia é o do fuso do dado, lido da coluna `ServerTimezone`.

## Organização das páginas

Toda página abre com o caminho, o título e, quando houver, a etiqueta de situação ao lado do título.
Abaixo do título vem a linha de fatos, com os itens separados por vírgula.
Abaixo de 900px o menu recolhe atrás de um botão na barra superior e abre por cima do conteúdo, com
o fundo escurecido. As tabelas rolam de lado dentro do cartão.

### Análise

1. **Caminho.** Turmas › turma › exercício › Análise. Só navega, sem etiqueta.
2. **Cabeçalho.** O nome do exercício, a etiqueta Treinado ao lado e a linha de fatos abaixo, com
   alunos, problemas, conceitos, execuções e a versão do modelo com a data do treino. A linha de
   fatos substitui a descrição fixa.
3. **Cartão de situação**, só antes do treino, com os três estados que o `AssignmentStateCards`
   implementa (sem conceitos aprovados, pronto para treinar e exercício que não treina).
4. **Cartão da análise**, com as abas Conceitos, Problemas e Alunos, nessa ordem. A aba Conceitos
   tem a vista "Tabela | Curva de aprendizagem" à direita das abas. O rodapé explica o marcador de
   estimado.
5. **Diálogo do aluno**, ao clicar numa linha da aba Alunos.

Observado e modelo se distinguem pela cor e pelo marcador `GeneratedByML`, sem cabeçalho agrupado e sem
linha da turma. Na aba Alunos, a coluna "Conceitos mais fracos" mostra três etiquetas com o nome
cortado e o valor, com o nome inteiro no hover. O painel lateral do aluno foi desenhado e ficou para
depois.

### Turmas

1. **Cabeçalho.** O título "Turmas", a linha de fatos com turmas e exercícios e "Nova turma" como
   botão primário à direita. A linha não soma alunos, porque duas turmas podem ter os mesmos alunos.
2. **Cartão das turmas**, com a busca no cabeçalho e a tabela com turma, exercícios, problemas,
   alunos, data de criação, situação e os botões de renomear e remover à direita.
3. **Atividade recente**, ao lado.

### Turma

1. **Caminho.** Turmas › turma.
2. **Cabeçalho.** O nome da turma, a etiqueta de situação ao lado, "Importar dados" como botão
   secundário à direita e a linha de fatos com alunos, problemas, exercícios, execuções e a data de
   criação.
3. **Execuções por dia**, a figura do semestre.
4. **Cartão da turma**, com as abas Exercícios e Alunos.
   - **Exercícios.** A tabela com exercício, período, alunos, execuções, taxa de acerto, situação e
     o botão de próximo passo. Conceitos e Análise de cada exercício continuam no menu.
   - **Alunos.** A tabela paginada com aluno, exercícios de que participou, problemas completados dos
     que tentou, execuções, taxa de acerto, erros de compilação, última atividade e domínio médio nos
     exercícios treinados, com "sem modelo" para quem não fez nenhum. A busca pelo identificador fica
     na faixa das abas.

### Conceitos

1. **Caminho.** Turmas › turma › exercício › Conceitos.
2. **Cabeçalho.** O nome do exercício, a etiqueta de situação ao lado e a linha de fatos com
   problemas, conceitos, a data da extração e quantos problemas estão sem conceito, este último como
   alerta em vermelho quando houver.
3. **Cartão dos conceitos**, com as abas Conceitos por problema e Problemas.
   - **Conceitos por problema.** A matriz, com os conceitos nas linhas e os problemas nas colunas, a
     recorrência de cada conceito à direita, quantos conceitos cada problema tem na última linha e as
     ações lupa, lápis e lixeira. A dica do número do problema traz a descrição com as estrelas. Novo
     conceito e Aprovar conceitos ficam à direita das abas, e o Aprovar fica desabilitado enquanto
     houver problema sem conceito.
   - **Problemas.** A tabela com problema, descrição e quantos conceitos cada um tem, com as estrelas
     antes do rótulo Descrição. Sem descrição, como no exercício extraído antes de a descrição
     existir, a célula mostra "sem descrição" em cinza.
4. **Origem do conceito**, o diálogo aberto pela lupa.

No exercício treinado a matriz é só consulta, com a lupa e sem lápis e lixeira. Pronto para
conceitos, o cartão é o estado vazio com os blocos e um único "Extrair conceitos".

### Importar dados

1. **Cabeçalho.** O título "Importar dados" e o indicador de passos à direita (Turma e arquivo,
   Processar, Conferir), sem frase de descrição.
2. **Passo 1**, em duas colunas com a mesma altura em todos os estados.
   - **Turma e arquivo**, com as pessoas e a pasta no título, a escolha da turma, que vem escolhida
     quando se chega pela página dela, e a caixa do pacote, que só abre com a turma escolhida. O
     rodapé traz a frase de apoio, Cancelar e Processar dados, que só habilita com os requisitos
     atendidos. Enquanto processa, o botão diz Processando e o formulário trava.
   - **O que o pacote precisa ter**, com a lista de requisitos (tabela de eventos, código dos
     alunos, formato ProgSnap2 v6 e até 512 MB) e um rodapé com o estado ("Envie o pacote para
     conferir os requisitos", "Tudo certo para processar", "Falta 1 requisito").
3. **Resultado.** A mensagem de sucesso com a linha de fatos (alunos, problemas, exercícios,
   submissões), Importar outros dados e Ver a turma como primário. Abaixo, a tabela de exercícios da
   Turma, com o próximo passo de cada um, e o cartão O que foi importado, com turma, arquivo, tabela
   usada e o que o sistema ajustou.

A recusa não grava nada. O requisito que faltou ganha o xis vermelho, e a caixa do pacote diz o que
fazer.

## Versões

| Versão | Data | O que mudou |
|---|---|---|
| 5, revista | 08/10/2026 | Correções antes da migração. Alinhamento igual em todas as tabelas, raio 0 sem token, `--color-text-inverse`, o texto do marcador do Code-DKT, os ícones de tela no menu com o `upload` em Importar dados e o exercício só com estatísticas sem ponto. A página de referência mantém o nome |
| 5 | 30/09/2026 | Importar dados. Requisitos do pacote no lugar das caixas vazias, caixa do pacote de altura fixa, ações no rodapé do cartão e o fim da barra fixa, passos em preto e cinza, resultado com a tabela de exercícios da Turma e os ajustes numa lista neutra |
| 4 | 30/09/2026 | Conceitos. Matriz problema × conceito com abas, origem do conceito com as soluções em abas de código, marcador `GeneratedByLLM` com as estrelas, dica com ?, vírgula na linha de fatos, estágios da extração em azul e a fonte mono só em bloco de código |
| 3 | 29/09/2026 | Turmas e Turma. Tabela de exercícios com próximo passo, alunos da turma com busca e paginação de 10, execuções por dia, atividade recente com treinos e extrações, e os ícones de Conceitos, Problemas e Treinado nas etiquetas de situação |
| 2 | 29/09/2026 | A organização da Análise. Linha de fatos, abas com Conceitos primeiro, curva de aprendizagem com dois eixos, cabeçalho de tabela com 32px e rótulo truncado, histograma da tabela sem eixo, menu que recolhe em tela estreita |
| 1 | 29/09/2026 | A primeira versão do design formal. Interface em cinza, azul só no modelo, raio 0, Public Sans na interface e Arial nos dados, componentes no estilo Carbon |

A cada versão, a página de referência é renomeada (`git mv`) para o número novo, e o git guarda as
anteriores. As iterações de design que levaram à versão 1 estão nos artifacts
[iteração de design 1](https://claude.ai/artifact/KqNSGX5HSt9MZi7yHQf1nP),
[iteração de design 2](https://claude.ai/artifact/LQwhxenEuDJ21oNZLAk7TK) e
[iteração de design 3](https://claude.ai/artifact/CQZsNUAHJXBUWXW9sZdW1R). A da versão 2 está em
[organização da Análise](https://claude.ai/artifact/VZeKyWCQVGZDrcsmDyqYUX), e a da versão 3 em
[Turmas e Turma](https://claude.ai/artifact/2AsBMzpMUcaQQPEcfwdU8q), e a da versão 4 em
[Conceitos](https://claude.ai/artifact/TskaC5xtKnyTjKiq3FwtGo), e a da versão 5 em
[Importar dados](https://claude.ai/artifact/Aeka6LFAfDiisWLk56Axjs).
