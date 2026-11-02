# Extração de referência do KCGen-KT no A439

A extração do exercício A439 na turma "CSEDM CodeWorkout Haiku", feita em 02/11/2026 pelas rotas da
API que a tela usa, com o código do commit `847c0d6`. Ela substitui a extração de referência de
06/10/2026, feita com o Sonnet 5.5, que continua no histórico do git (commit `653b1a2`). A troca do
modelo e o estudo que a motivou estão na linha 9 do KCGen-KT no `DEVELOPMENT.md` e em
[kcgen_kt_haiku_niveis_de_abstracao.md](kcgen_kt_haiku_niveis_de_abstracao.md).

## Como foi feita

- O pacote importado tem a `MainTable.csv` e o `CodeStates.csv` da variante CodeWorkout da CSEDM e
  a planilha oficial de enunciados, e os 50 problemas da turma ganharam enunciado.
- O modelo de linguagem é o `claude-haiku-4-5-20251001`, com a versão `kcgen-v2` dos prompts. Os
  vetores das soluções saem do `microsoft/codebert-base` (revisão `3b0952f`) e os dos nomes de KC do
  `all-MiniLM-L6-v2` (revisão `1110a24`).
- Na turma, o A439 é o exercício 31, e a extração foi o job 10.
- As soluções amostradas são as mesmas da extração de 06/10/2026, porque o sorteio não depende do
  modelo de linguagem.
- Os trechos de cada conceito e o código completo das soluções que o LLM leu estão em
  [kcgen_kt_a439_evidence.md](kcgen_kt_a439_evidence.md).

## Números

| Item | Resultado |
|---|---|
| Tempo | 12 min 41 s |
| KCs candidatos | 65, de 4 a 14 por problema |
| Nomes únicos | 26 |
| Grupos, 50/103 dos nomes únicos | 13 |
| Conceitos | 13, sem grupos fundidos por nome |
| Vínculos problema × conceito | 46, de 3 a 9 por problema |
| Respostas do LLM guardadas no cache | 26, sendo 10 da geração, 5 da nomeação, 10 dos trechos e 1 da tradução |
| Trechos gravados | 46 de 46 |

O cache guarda só as respostas válidas, então uma tentativa repetida não aparece na contagem.

## Os problemas

| Problema | Método | KCs candidatos | Conceitos |
|---|---|---|---|
| 1 | `sortaSum` | 4 | 4 |
| 3 | `in1To10` | 7 | 4 |
| 5 | `answerCell` | 5 | 4 |
| 12 | `squirrelPlay` | 8 | 4 |
| 13 | `caughtSpeeding` | 6 | 5 |
| 232 | `alarmClock` | 5 | 4 |
| 233 | `love6` | 6 | 5 |
| 234 | `cigarParty` | 14 | 9 |
| 235 | `dateFashion` | 4 | 3 |
| 236 | `greenTicket` | 6 | 4 |

## Os 13 conceitos

O nome mostrado é a tradução do nome gerado, que é o resultado do método, em inglês e em
minúsculas.

| Conceito | Nome gerado | Problemas |
|---|---|---|
| Estruturas de instrução if-else | `if-else statement structures` | todos os 10 |
| Operadores lógicos e condicionais | `logical and conditional operators` | todos os 10 |
| Comparações numéricas | `numerical comparisons` | 1, 3, 12, 13, 232, 233, 234, 235, 236 |
| Operações aritméticas básicas | `basic arithmetic operations` | 1, 13, 233, 234, 236 |
| Uso do tipo de dado boolean | `boolean data type usage` | 3, 13, 232 |
| Inicialização e atribuição de variável | `variable initialization and assignment` | 5, 12 |
| Métodos básicos de string | `basic string methods` | 234 |
| Método Math.abs() | `math.abs() method` | 234 |
| Invocação de método | `method invocation` | 233 |
| Operador de incremento de variável | `variable increment operator` | 234 |
| Operador de módulo | `modulo operator` | 234 |
| Instrução de retorno | `return statement` | 5 |
| Precedência de operador e parênteses | `operator precedence and parentheses` | 234 |

## Observações

- A extração de 06/10/2026, com o Sonnet 5.5, deu 93 candidatos, 51 nomes únicos, 25 conceitos e 84
  vínculos, de 6 a 11 por problema. O TCC 1 tinha 15 conceitos no A439, e a planilha oficial marca 7
  tags humanas, de 3 a 6 por problema.
- Os grupos juntam variações do mesmo construto. O if e else junta "If and else statement", "Nested
  if statement", "If-else if-else chain" e "Else if statement", e os operadores lógicos juntam o AND,
  o OR, o NOT e o operador ternário.
- O problema 234 (`cigarParty`) tem 14 candidatos e 9 conceitos porque a solução 5 sorteada, de
  `CodeStateID` `1750294`, é uma execução correta de 247 linhas em que o aluno colou 24 métodos de
  outros problemas. Os conceitos de String, de `Math.abs`, de módulo e de incremento só aparecem
  nela, e os trechos deles apontam para essa solução. A extração do Sonnet leu a mesma solução.
- O tempo foi de 12 min 41 s, contra 2 min 15 s da extração com o Sonnet 5.5, com a mesma
  concorrência de quatro chamadas.
