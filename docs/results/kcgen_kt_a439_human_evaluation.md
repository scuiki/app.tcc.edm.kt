# Avaliação humana do KCGen-KT no A439

A planilha de anotação da etapa 9 do `KCGEN_KT_PLAN.md`, com a rubrica da avaliação humana do
paper (§5, p. 33413 (PDF 9), e Apêndice F, p. 33418 (PDF 14)), sobre a extração de referência do
A439. Os conceitos gerados saem de `tests/data/kc/a439_reference_extraction.json`, em inglês, como
o método os produz. As tags humanas saem da planilha oficial de enunciados, em
`tests/data/csedm_problem_statements`, com os nomes em inglês que o repositório do paper dá às 18
colunas (a lista `nat_lan_ls` do `KC_gen.py`). O código das soluções que o LLM leu e os trechos de
cada conceito estão em [kcgen_kt_a439_evidence.md](kcgen_kt_a439_evidence.md).

## Como anotar

São as três tarefas do paper. Cada célula vazia recebe uma das respostas entre crases.

1. **Interpretabilidade.** Cada conceito gerado e cada tag humana recebe `sim` se é claramente
   compreensível do ponto de vista de um professor, e `não` se não é. Cada um é julgado uma vez,
   e não em cada problema em que aparece.
   > For each KC, indicate whether it is clearly understandable from an instructor's perspective
   > to decide the KC's interpretability using Yes or No.
2. **Precisão.** Em cada problema, cada conceito gerado e cada tag humana recebe `sim` se é
   relevante para aquele problema, e `não` se não é.
   > For each KC associated with a problem, indicate whether it is relevant to that problem in
   > binary format (relevant/irrelevant).
3. **Cobertura.** Em cada problema, os conceitos gerados recebem `menor` se cobrem menos KCs
   essenciais que as tags humanas, e `igual ou maior` se cobrem tanto quanto elas ou mais. Quando
   cada conjunto tem KCs que faltam no outro e nenhum domina, a resposta é `igual ou maior`.
   > Label "Less coverage" if Set 1 covers fewer relevant KCs than Set 2 and label
   > "Equal-or-greater coverage" if Set 1 covers more relevant KCs than Set 2. If both sets
   > contain unique KCs that the other is missing which means neither list clearly dominates,
   > select equal-or-greater coverage.

O problema 13 (`caughtSpeeding`) é o exemplo 2 do prompt de geração, com as tags humanas dele
como os KCs esperados, então os conceitos gerados dele não são independentes das tags. Ele é
anotado como os outros, porque estava entre os 50 problemas do paper, e o relatório mostra os
números com ele e sem ele.

São 13 conceitos e 7 tags para a interpretabilidade, 46 vínculos gerados
e 44 vínculos de tags para a precisão, e 10 problemas para a cobertura.

## Interpretabilidade

### Os 13 conceitos gerados

| Conceito gerado | Problemas | Interpretável |
|---|---|---|
| `if-else statement structures` | todos os 10 | |
| `logical and conditional operators` | todos os 10 | |
| `numerical comparisons` | 1, 3, 12, 13, 232, 233, 234, 235, 236 | |
| `basic arithmetic operations` | 1, 13, 233, 234, 236 | |
| `boolean data type usage` | 3, 13, 232 | |
| `variable initialization and assignment` | 5, 12 | |
| `basic string methods` | 234 | |
| `math.abs() method` | 234 | |
| `method invocation` | 233 | |
| `variable increment operator` | 234 | |
| `modulo operator` | 234 | |
| `return statement` | 5 | |
| `operator precedence and parentheses` | 234 | |

### As 7 tags humanas que aparecem no A439

As outras 12 das 18 colunas da planilha não marcam nenhum problema do A439.

| Tag humana | Coluna da planilha | Problemas | Interpretável |
|---|---|---|---|
| `If and else statement` | `If/Else` | todos os 10 | |
| `Logical operators` | `LogicAndNotOr` | 1, 3, 12, 13, 232, 233, 234, 235, 236 | |
| `Numerical comparisons` | `LogicCompareNum` | 1, 3, 12, 13, 232, 233, 234, 235, 236 | |
| `Nested if statement` | `NestedIf` | 3, 5, 12, 13, 232, 234 | |
| `Boolean operations` | `LogicBoolean` | 3, 5, 12, 13, 232, 234 | |
| `Basic arithmetic operations` | `Math+-*/` | 1, 13, 233 | |
| `String formatting` | `StringFormat` | 232 | |

## Precisão e cobertura, problema a problema

### Problema 1, `sortaSum`

> Write a function in Java that implements the following logic: Given 2 ints, a and b, return their sum. However, sums in the range 10..19 inclusive, are forbidden, so in that case just return 20.

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |
| `basic arithmetic operations` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |
| `Basic arithmetic operations` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 3, `in1To10`

> Write a function in Java that implements the following logic: Given a number n, return true if n is in the range 1..10, inclusive. Unless "outsideMode" is true, in which case return true if the number is less or equal to 1, or greater or equal to 10.

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |
| `boolean data type usage` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |
| `Nested if statement` | |
| `Boolean operations` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 5, `answerCell`

> Write a function in Java that implements the following logic: Your cell phone rings. Return true if you should answer it. Normally you answer, except in the morning you only answer if it is your mom calling. In all cases, if you are asleep, you do not answer.

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `variable initialization and assignment` | |
| `return statement` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Nested if statement` | |
| `Boolean operations` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 12, `squirrelPlay`

> Write a function in Java that implements the following logic: The squirrels in Palo Alto spend most of the day playing. In particular, they play if the temperature is between 60 and 90 (inclusive). Unless it is summer, then the upper limit is 100 instead of 90. Given an int temperature and a boolean isSummer, return true if the squirrels play and false otherwise.

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |
| `variable initialization and assignment` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |
| `Nested if statement` | |
| `Boolean operations` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 13, `caughtSpeeding`

> Write a function in Java that implements the following logic: You are driving a little too fast, and a police officer stops you. Write code to compute the result, encoded as an int value: 0=no ticket, 1=small ticket, or 2=big ticket. If speed is 60 or less, the result is 0. If speed is between 61 and 80 inclusive, the result is 1. If speed is 81 or more, the result is 2. Unless it is your birthday--on that day, your speed can be 5 higher in all cases.

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |
| `basic arithmetic operations` | |
| `boolean data type usage` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |
| `Nested if statement` | |
| `Boolean operations` | |
| `Basic arithmetic operations` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 232, `alarmClock`

> Given a day of the week encoded as 0 = Sun, 1 = Mon, 2 = Tue, ... 6 = Sat, and a boolean indicating if we are on vacation, return a string of the form "7:00" indicating when the alarm clock should ring. Weekdays, the alarm should be "7:00" and on the weekend it should be "10:00". Unless we are on vacation--then on weekdays it should be "10:00" and weekends it should be "off".

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |
| `boolean data type usage` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |
| `Nested if statement` | |
| `Boolean operations` | |
| `String formatting` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 233, `love6`

> The number 6 is a truly great number. Given two int values, a and b, return true if either one is 6. Or if their sum or difference is 6. Note: the function Math.abs(num) computes the absolute value of a number.

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |
| `basic arithmetic operations` | |
| `method invocation` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |
| `Basic arithmetic operations` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 234, `cigarParty`

> When squirrels get together for a party, they like to have cigars. A squirrel party is successful when the number of cigars is between 40 and 60, inclusive. Unless it is the weekend, in which case there is no upper bound on the number of cigars. Return true if the party with the given values is successful, or false otherwise.

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |
| `basic arithmetic operations` | |
| `basic string methods` | |
| `math.abs() method` | |
| `variable increment operator` | |
| `modulo operator` | |
| `operator precedence and parentheses` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |
| `Nested if statement` | |
| `Boolean operations` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 235, `dateFashion`

> You and your date are trying to get a table at a restaurant. The parameter you is the stylishness of your clothes, in the range 0..10, and date is the stylishness of your date's clothes. Write a method that returns your chances of getting a table, encoded as an int value with 0 = no, 1 = maybe, 2 = yes. If either of you is very stylish, 8 or more, then the result is 2 (yes). With the exception that if either of you has style of 2 or less, then the result is 0 (no). Otherwise the result is 1 (maybe).

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |

### Problema 236, `greenTicket`

> You have a green lottery ticket, with ints a, b, and c on it. If the numbers are all different from each other, the result is 0. If all of the numbers are the same, the result is 20. If two of the numbers are the same, the result is 10.

| Conceito gerado | Relevante |
|---|---|
| `if-else statement structures` | |
| `logical and conditional operators` | |
| `numerical comparisons` | |
| `basic arithmetic operations` | |

| Tag humana | Relevante |
|---|---|
| `If and else statement` | |
| `Logical operators` | |
| `Numerical comparisons` | |

| Cobertura dos conceitos gerados frente às tags humanas | `menor` ou `igual ou maior` |
|---|---|
| | |
