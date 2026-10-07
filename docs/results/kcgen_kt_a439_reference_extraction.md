# Extração de referência do KCGen-KT no A439

A extração do exercício A439 na turma "CSEDM CodeWorkout, referência do KCGen-KT", feita em
06/10/2026 pelas rotas da API que a tela usa, com o código do commit `b5278ac`. É a extração de
referência da etapa 7 do `KCGEN_KT_PLAN.md`, e os outros quatro exercícios da turma saem pela
aplicação, como o Leo decidiu em 07/10/2026.

## Como foi feita

- O pacote importado tem a `MainTable.csv` e o `CodeStates.csv` da variante CodeWorkout da CSEDM e
  a planilha oficial de enunciados, e os 50 problemas da turma ganharam enunciado.
- O modelo de linguagem é o `claude-sonnet-5-5`, com a versão `kcgen-v2` dos prompts. Os vetores
  das soluções saem do `microsoft/codebert-base` (revisão `3b0952f`) e os dos nomes de KC do
  `all-MiniLM-L6-v2` (revisão `1110a24`).
- Na turma, o A439 é o exercício 8, e a extração foi o job 5.
- Os trechos de cada conceito e o código completo das soluções que o LLM leu estão em
  [kcgen_kt_a439_evidence.md](kcgen_kt_a439_evidence.md).

## Números

| Item | Resultado |
|---|---|
| Tempo | 2 min 15 s |
| KCs candidatos | 93, de 7 a 12 por problema |
| Nomes únicos | 51 |
| Grupos, 50/103 dos nomes únicos | 25 |
| Conceitos | 25, sem grupos fundidos por nome |
| Vínculos problema × conceito | 84 |
| Respostas do LLM guardadas no cache | 33, sendo 10 da geração, 12 da nomeação, 10 dos trechos e 1 da tradução |
| Trechos gravados | 83 de 84 |

O cache guarda só as respostas válidas, então uma tentativa repetida não aparece na contagem.

## Os problemas

| Problema | Método | KCs candidatos | Conceitos |
|---|---|---|---|
| 1 | `sortaSum` | 8 | 8 |
| 3 | `in1To10` | 7 | 6 |
| 5 | `answerCell` | 10 | 9 |
| 12 | `squirrelPlay` | 10 | 9 |
| 13 | `caughtSpeeding` | 12 | 11 |
| 232 | `alarmClock` | 10 | 9 |
| 233 | `love6` | 10 | 9 |
| 234 | `cigarParty` | 9 | 8 |
| 235 | `dateFashion` | 9 | 8 |
| 236 | `greenTicket` | 8 | 7 |

## Os 25 conceitos

O nome mostrado é a tradução do nome gerado, que é o resultado do método, em inglês e em
minúsculas.

| Conceito | Nome gerado | Problemas |
|---|---|---|
| Instruções condicionais: if/else, encadeamento de else if e if aninhado | `conditional statements: if/else, else-if chaining, and nested if` | todos os 10 |
| Operadores lógicos (e, ou) | `logical operators (and, or)` | todos os 10 |
| Definição de método e instruções return | `method definition and return statements` | 1, 3, 5, 12, 13, 234, 235, 236 |
| Comparações numéricas (operadores relacionais) | `numerical comparisons (relational operators)` | 1, 3, 12, 13, 232, 234, 235 |
| Variáveis, condições e operações boolean | `boolean variables, conditions, and operations` | 3, 5, 12, 13, 232, 234 |
| Declaração e atribuição de variáveis | `variable declaration and assignment` | 1, 12, 13, 232, 233 |
| Instruções return e retorno antecipado | `return statements and early return` | 5, 13, 233, 235, 236 |
| Encadeamento de else if e condicionais de múltiplos ramos | `else-if chains and multi-branch conditionals` | 5, 13, 232, 235 |
| Operações aritméticas básicas | `basic arithmetic operations` | 1, 13, 233, 236 |
| Retorno de valores boolean | `returning boolean values` | 3, 12, 233, 234 |
| Comparação numérica de igualdade e desigualdade | `numerical equality and inequality comparison` | 232, 233, 236 |
| Operador condicional ternário | `ternary conditional operator` | 1, 12, 13 |
| Ordem das condições e precedência das regras | `condition ordering and precedence of rules` | 5, 235 |
| Tratamento de limites inclusivos e exclusivos | `inclusive and exclusive boundary handling` | 1, 235 |
| Análise de casos e ordem das condições | `case analysis and ordering of conditions` | 236 |
| Atribuição de variável boolean e valor padrão | `boolean variable assignment and default value` | 5 |
| Mapeamento de valores inteiros codificados para categorias | `mapping encoded integer values to categories` | 232 |
| Operador lógico de negação | `logical not operator` | 5 |
| Precedência de operadores e parênteses | `operator precedence and parentheses` | 234 |
| Reatribuição de parâmetros de método | `reassigning method parameters` | 13 |
| Retorno antecipado e fluxo de controle | `early return and control flow` | 234 |
| Retorno de valores de um método / literais String | `returning values from a method / string literals` | 232 |
| Tratamento de casos simétricos ou independentes da ordem | `handling symmetric or order-independent cases` | 233 |
| Valor absoluto com math.abs | `absolute value with math.abs` | 233 |
| Valor padrão com sobrescrita condicional | `default value with conditional override` | 12 |

## Observações

- O paper tem 103 nomes únicos e 50 conceitos para os 50 problemas da CodeWorkout juntos. Aqui são
  51 nomes e 25 conceitos para os 10 problemas do A439, porque o agrupamento é por exercício, e
  sobra mais nome e mais conceito por problema, como a justificativa 19 do KCGen-KT no
  `DEVELOPMENT.md` previa. O TCC 1 tinha 15 conceitos no A439.
- Há conceitos parecidos, como os três de return, os dois de ordem das condições e os de boolean. É
  o efeito de 25 grupos para 51 nomes, e o professor junta ou remove os parecidos na revisão.
- O nome gerado vai para minúsculas, como no repositório do Duan (linha 25 do KCGen-KT no
  `DEVELOPMENT.md`), e com isso o `Math.abs` do Java virou `math.abs`, que a tradução manteve.
- A tradução de "logical operators (and, or)" saiu "Operadores lógicos (e, ou)", e `&&` e `||`
  talvez fossem mais claros.
- O trecho descartado é do problema 233 (`love6`), no conceito "handling symmetric or
  order-independent cases". O LLM juntou duas partes da solução que não são linhas seguidas, o app
  não achou o trecho na solução, e o conceito ficou ligado ao problema sem trecho.
