# Design

As regras visuais do app docente. O porquê de cada decisão fica em `DECISIONS.md`, na seção
Frontend. Os valores (hex, sombras, medidas) ficam no `src/web/src/styles/tokens.css`, e aqui cada
papel é citado pelo nome do token.

**Versão 3, 29/09/2026.** Referência visual em [`design/design-system-v3.html`](design/design-system-v3.html),
que abre direto no navegador.

**Estado.** Este documento é a especificação. O `tokens.css` e os componentes ainda seguem a
linguagem anterior (azul de ação, Open Sans com Arial nas tabelas, raio de 2px), e Análise, Turmas e
Turma ainda têm a organização antiga. Tudo será migrado depois da rodada das páginas. Até lá, os valores
estão na página de referência, e os nomes de token abaixo são os planejados.

## Princípios

- **Entregar o dado, não a interpretação.** Sem níveis, faixas ou cores de alerta sobre um número.
  O professor ordena e lê.
- **Azul significa modelo.** O azul só aparece quando existe um Code-DKT por trás do que está na
  tela. Botão, link, foco, menu e abas não são azuis.
- **Três papéis de cor.** Cinza para a interface, azul para o modelo, vermelho para erro e
  exclusão. Não há verde nem âmbar.
- **Sombra marca objeto.** Só o cartão, o diálogo e a barra superior têm sombra. Nada dentro deles.
- **Raio 0.** Botões, campos, cartões, etiquetas, barras e histogramas têm canto vivo. Só os pontos
  de situação e o marcador de estimado são redondos.
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
| Modelo | `--color-model` | Domínio, distribuição, curva de perda, ponto de treinado, estágios do treino |
| | `--color-model-strong` | Hover das marcas do modelo, texto sobre o azul claro |
| | `--color-model-soft` e `--color-model-soft-border` | Etiqueta Treinado, fundo do marcador de estimado |
| Observado | `--color-observed` | Taxa de acerto e toda barra do que aconteceu |
| | `--color-bar-track` | Trilho das barras |
| Erro | `--color-danger` | Ícone de erro, contorno de campo com erro, botão destrutivo |
| | `--color-danger-text` | Texto de erro, hover do destrutivo |

A migração troca `--color-accent`, `--color-accent-soft`, `--color-accent-soft-border` e
`--color-accent-text` por `--color-primary` e pelos tokens de modelo, e `--color-bar-observed` e
`--color-bar-predicted` por `--color-observed` e `--color-model`.

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
A migração troca `--font-mono` e `--font-table` por `--font-data`.

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
| `--radius` | 0 | Tudo, exceto pontos de situação e marcador de estimado |
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
quando aguarda conceitos, meio preenchido com os conceitos aprovados e em `--color-model` quando
existe um modelo treinado.

**Abas.** A aba ativa tem texto `--color-text` em 600 e traço de 2px na mesma cor. A faixa das abas
é branca, igual ao cartão.

**Cartão.** Branco, com `--shadow-card` e sem borda, com cabeçalho próprio de 48px e fio abaixo
dele. O rodapé opcional tem 44px e texto de apoio.

**Diálogo.** O `<dialog>` nativo, com `--shadow-dialog` sobre o fundo escurecido. O rodapé é
`--color-surface-subtle`, com as ações à direita e a principal por último.

**Área de soltar arquivo.** Contorno tracejado em `--color-control-border`. Com o arquivo por cima,
o contorno fica sólido em `--color-text` e o fundo `--color-hover`. Importar dados vem antes de
qualquer modelo, então a área não tem azul.

**Lista de estágios.** Duas variantes pela origem do trabalho. A neutra, em `--color-text`, serve a
extração de conceitos, que é feita pelo LLM. A de modelo, em `--color-model`, serve o treino do
Code-DKT.

**Carregamento e vazio.** O giro de carregamento é `--color-text`. O estado vazio tem o ícone num
quadrado `--color-hover`, um título e uma frase de apoio.

**Mensagem de resultado.** O erro tem ícone `--color-danger` e título `--color-danger-text`. O
sucesso é neutro, com o ícone em `--color-text`.

**Marcador de estimado.** O cérebro em `--color-model-strong` sobre um círculo `--color-model-soft`,
antes do rótulo de toda coluna que vem do modelo.

**Dica e balão.** A dica é o ícone de alerta em `--color-text-muted`. O balão é `--color-text` com
texto branco, sem raio, e aparece no hover ou no foco pelo `Tooltip`, nunca pelo `title` nativo.

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
o mesmo ícone em todo lugar. O menu mantém o ponto de situação e não usa os ícones de etapa, para a
lista longa ficar discreta.

| Ícone (lucide) | Representa | Onde |
|---|---|---|
| `blocks` | Conceitos | Menu, aba, botões e etiquetas das etapas de conceitos |
| `file-code` | Problemas | Aba Problemas da Análise |
| `brain` | O modelo | Marcador de estimado, etiqueta Treinado, evento de treino |
| `chart-column` | Análise | Menu e botão "Ver análise" |
| `clipboard-pen` | Exercício | Menu e aba Exercícios |
| `users` | Turmas e alunos | Menu, aba Alunos, evento de turma criada |
| `upload` | Importar dados | Botão do cabeçalho da turma |

## Tabelas

- A tabela inteira usa `--font-data`.
- Sem fio vertical. Traço `--color-text` sob o cabeçalho e no fim da tabela, fio `--color-rule`
  entre as linhas, em todas as tabelas.
- Linha e cabeçalho com a mesma altura, 32px. Um rótulo longo trunca com reticências e mostra o
  texto inteiro no hover, e em tela larga aparece inteiro.
- O histograma da tabela não tem eixo. A escala fica na dica do cabeçalho, e a faixa sem aluno é um
  traço de 1px em `--color-control-border`.
- Na Análise, o nome fica à esquerda e os números centralizados sob rótulos centralizados. Nas
  demais tabelas, tudo fica à esquerda, e só a coluna de botões fica à direita.
- A taxa de acerto usa a barra em `--color-observed`. Domínio e distribuição usam `--color-model`
  e levam o marcador de estimado no rótulo.
- As barras e os histogramas das tabelas são CSS, com canto vivo.

## Gráficos

- Uma figura só entra quando mostra um dado que a tabela não tem. Redesenhar os números da tabela
  em outra forma não é motivo para uma figura.
- A figura inteira usa `--font-data`, para entrar na monografia como está.
- Cada figura tem título, subtítulo com a unidade e a fonte do dado (por exemplo, "Fonte: Code-DKT
  versão 5").
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
Abaixo de 900px o menu recolhe atrás de um botão na barra superior e abre por cima do conteúdo, com
o fundo escurecido. As tabelas rolam de lado dentro do cartão.

### Análise

1. **Caminho.** Turmas › turma › exercício › Análise. Só navega, sem etiqueta.
2. **Cabeçalho.** O nome do exercício, a etiqueta Treinado ao lado e a linha de fatos abaixo, com
   alunos, problemas, conceitos, execuções e a versão do modelo com a data do treino. A linha de
   fatos substitui a descrição fixa.
3. **Cartão de situação**, só antes do treino, como hoje.
4. **Cartão da análise**, com as abas Conceitos, Problemas e Alunos, nessa ordem. A aba Conceitos
   tem a vista "Tabela | Curva de aprendizagem" à direita das abas. O rodapé explica o marcador de
   estimado.
5. **Diálogo do aluno**, ao clicar numa linha da aba Alunos.

Observado e modelo se distinguem pela cor e pelo marcador de estimado, sem cabeçalho agrupado e sem
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

## Versões

| Versão | Data | O que mudou |
|---|---|---|
| 3 | 29/09/2026 | Turmas e Turma. Tabela de exercícios com próximo passo, alunos da turma com busca e paginação de 10, execuções por dia, atividade recente com treinos e extrações, e os ícones de Conceitos, Problemas e Treinado nas etiquetas de situação |
| 2 | 29/09/2026 | A organização da Análise. Linha de fatos, abas com Conceitos primeiro, curva de aprendizagem com dois eixos, cabeçalho de tabela com 32px e rótulo truncado, histograma da tabela sem eixo, menu que recolhe em tela estreita |
| 1 | 29/09/2026 | A linguagem formal. Interface em cinza, azul só no modelo, raio 0, Public Sans na interface e Arial nos dados, componentes no estilo Carbon |

A cada versão, a página de referência é renomeada (`git mv`) para o número novo, e o git guarda as
anteriores. As rodadas que levaram à versão 1 estão nos artifacts
[rodada 1](https://claude.ai/artifact/KqNSGX5HSt9MZi7yHQf1nP),
[rodada 2](https://claude.ai/artifact/LQwhxenEuDJ21oNZLAk7TK) e
[rodada 3](https://claude.ai/artifact/CQZsNUAHJXBUWXW9sZdW1R). A da versão 2 está em
[organização da Análise](https://claude.ai/artifact/VZeKyWCQVGZDrcsmDyqYUX), e a da versão 3 em
[Turmas e Turma](https://claude.ai/artifact/2AsBMzpMUcaQQPEcfwdU8q).
