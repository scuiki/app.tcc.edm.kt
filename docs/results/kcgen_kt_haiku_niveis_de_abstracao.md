# KCGen-KT com o Haiku 4.5 nos níveis de abstração do Duan

Um estudo de 02/11/2026 sobre o excesso de conceitos da extração com o Sonnet 5.5. A geração dos KCs
candidatos roda com o `claude-haiku-4-5-20251001`, e os nomes únicos de cada exercício são agrupados
nos cinco níveis de abstração que Duan et al. testaram. O resultado é comparado com as tags humanas
da planilha oficial da CSEDM, com o que o paper reporta, com o TCC 1 e com as extrações do Sonnet.
Nada no app mudou, e o estudo não é uma decisão. Os candidatos gerados e as medidas estão em
[kcgen_kt_haiku_niveis_de_abstracao.json](kcgen_kt_haiku_niveis_de_abstracao.json).

## Como foi feito

- **Geração.** Só a etapa 2 do KCGen-KT, com o prompt `kcgen-v2` e as mesmas 5 soluções que o app
  amostra, conferidas contra as amostras gravadas do Sonnet onde elas existem. Os exercícios são os
  da turma 6, "CSEDM CodeWorkout", que têm enunciado em todos os problemas. O A439 tem duas
  execuções, de 24/10/2026, e os outros quatro uma, de 02/11/2026. O A502 tem ainda duas execuções
  sem enunciado, de 24/10/2026, para comparar com as extrações do Sonnet, que rodaram sem ele.
- **Agrupamento.** O SBERT e o HAC do app, sem a nomeação pelo LLM. A medida é feita sobre os grupos
  do HAC, então dois grupos que receberiam o mesmo nome contam como dois. Nomes iguais a menos de
  maiúsculas e minúsculas contam como um nome só, e a tabela dos exercícios mostra quantos nomes
  isso juntou.
- **Níveis.** Os cinco números de grupos que o paper testou na CodeWorkout, 100, 75, 50, 20 e 10
  para 103 nomes únicos (§5.1.2 da v3 do arXiv), aplicados como fração dos nomes únicos de cada
  exercício e arredondados. O nível 50 é o que o paper escolheu e o que o app usa hoje (decisão 19
  do KCGen-KT no `DEVELOPMENT.md`).
- **Medidas.** Conceitos no exercício, conceitos por problema, pares de conceitos ligados exatamente
  aos mesmos problemas, que mostram o mesmo domínio para todo aluno no dashboard, e a maior distância
  de cosseno entre dois nomes do mesmo grupo. Acima de uns 0,6 o grupo já junta ideias diferentes.
- **Referências.** As tags humanas são as 18 da planilha oficial, "one researcher's judgement" na
  página do dataset. O TCC 1 são os `results/qmatrix_A*.csv`, `kc_descriptions_A*.json` e
  `kc_raw_A*.json` do commit `0e8807c`. O paper foi lido na v3 do arXiv (2502.18632v3). As tabelas
  citadas são as da v3, e no ACL a Tabela 6 da v3 é a 7 e a 10 é a 11.
- **Sonnet.** As extrações 5 e 9 do A439, com enunciado, e 6 e 7 do A502, sem enunciado. Os outros
  três exercícios não têm extração do Sonnet.

## O conjunto dos 50 problemas

O paper conta os nomes dos 50 problemas da CodeWorkout juntos, e esta é a única contagem dele que dá
para repetir.

| Origem | Candidatos | Nomes únicos nos 50 problemas |
|---|:---:|:---:|
| Duan, GPT-4o (§5.1.2) | não informado | 103 |
| Haiku 4.5 | 463 | 125 |
| TCC 1, Haiku 4.5 com o prompt próprio e 1 solução | 292 | 278 |

O paper não informa quantos KCs cada problema tem, nem antes nem depois do agrupamento.

## Os cinco exercícios

Os conceitos e as medidas do Haiku são dos níveis 50 e 20, e os demais níveis estão no JSON. No A439
os números do Haiku e do Sonnet aparecem para as duas execuções.

| Exercício | Tags humanas | TCC 1 | Sonnet, nível 50 | Haiku, nível 50 | Haiku, nível 20 |
|---|:---:|:---:|:---:|:---:|:---:|
| A439, conceitos | 7 | 15 | 25 e 24 | 12 e 12 | 5 e 5 |
| A439, por problema | 4,4 | 4,8 | 8,4 e 7,9 | 4,6 e 4,8 | 2,6 e 2,5 |
| A487, conceitos | 13 | 15 | | 17 | 7 |
| A487, por problema | 5,0 | 4,4 | | 5,2 | 3,2 |
| A492, conceitos | 13 | 15 | | 27 | 11 |
| A492, por problema | 6,8 | 3,9 | | 10,3 | 5,6 |
| A494, conceitos | 8 | 15 | | 19 | 8 |
| A494, por problema | 5,3 | 4,8 | | 8,3 | 5,1 |
| A502, conceitos | 10 | 12 | 44 e 50, sem enunciado | 22 | 9 |
| A502, por problema | 4,6 | 3,6 | 13,0 e 13,5, sem enunciado | 8,2 | 4,6 |

| Exercício | Pares com os mesmos problemas, humanas | TCC 1 | Haiku, nível 50 | Haiku, nível 20 | Maior distância num grupo, Haiku, nível 50 | Haiku, nível 20 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| A439 | 2 | 1 | 11 e 7 | 0 e 0 | 0,52 e 0,48 | 0,79 e 0,79 |
| A487 | 4 | 3 | 3 | 1 | 0,46 | 0,86 |
| A492 | 1 | 1 | 14 | 3 | 0,51 | 0,75 |
| A494 | 2 | 0 | 7 | 4 | 0,49 | 0,92 |
| A502 | 3 | 0 | 10 | 3 | 0,50 | 0,89 |

| Exercício | Candidatos por problema, TCC 1 | Sonnet | Haiku | Nomes únicos, TCC 1 | Sonnet | Haiku, antes e depois de juntar a caixa | Nomes de um problema só, Haiku |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A439 | 5,8 | 9,3 e 9,5 | 6,7 e 6,7 | 52 | 51 e 50 | 25 e 25, sem mudança | 14 e 15 |
| A487 | 5,5 | | 7,4 | 55 | | 36, sem mudança | 19 |
| A492 | 5,9 | | 12,2 | 58 | | 58 e 55 | 38 |
| A494 | 6,0 | | 10,0 | 59 | | 57 e 40 | 21 |
| A502 | 6,0 | 13,3 e 14,5, sem enunciado | 10,0 | 59 | 90 e 104 | 60 e 46 | 29 |

Sem enunciado, o Haiku deu 49 e 45 nomes no A502, 24 e 22 conceitos no nível 50 e 8,6 e 9,3
conceitos por problema, perto da execução com enunciado.

## Três problemas lado a lado

O paper publica os KCs gerados de dois problemas. No sortaSum, a lista da Tabela 10 é a de um prompt
de rotulagem, que o paper chama de "a predefined list of general programming knowledge components"
e não diz que foi gerada. Os KCs do Haiku no nível 50 aparecem agrupados como o HAC os juntou, e os
do Sonnet são os candidatos, antes do agrupamento.

### love6 (A439, problema 233)

| Origem | KCs |
|---|---|
| Duan, gerados (Tabela 1) | If and else if statement, Basic arithmetic operations, Logical operators, Numerical comparisons, Absolute value computation |
| Tags humanas (Tabela 1 e planilha) | If/Else, Math+-*/, LogicAndNotOr, LogicCompareNum |
| TCC 1 | Equality comparison of numeric values, Absolute value for comparison operations, Using arithmetic operations in conditionals, Compound boolean expressions with logical operators, Early return pattern in control flow, Method return types and values |
| Sonnet, candidatos | If and else statement, Else-if chaining and nested if statements, Numerical equality comparison, Logical OR operator, Basic arithmetic operations, Absolute value with Math.abs, Boolean return values, Early return and default return, Local variable declaration and assignment, Handling symmetric or order-independent cases |
| Haiku, nível 50 (6 conceitos) | [If and else statement, Nested if statement, Else-if statement], Logical operators, Numerical comparisons, Basic arithmetic operations, Math.abs() function, Variable declaration and assignment |
| Haiku, nível 20 (4 conceitos) | [If and else statement, Logical operators, Nested if statement, Else-if statement, Variable declaration and assignment], Numerical comparisons, Basic arithmetic operations, Math.abs() function |

### has77 (A494, problema 67)

| Origem | KCs |
|---|---|
| Duan, gerados (Tabela 6) | For loop iteration, Array indexing and assignment, Boolean logic, Logical operators, Numerical comparisons, If and else if statement |
| Tags humanas | If/Else, For, Math+-*/, LogicAndNotOr, LogicCompareNum, ArrayIndex |
| TCC 1 | Array manipulation using indexed access, Method return types and values, Early exit with conditional return, Conditional logic and logical operators |
| Haiku, nível 50 (9 conceitos) | [For loop, While loop], Array indexing, Array length, Numerical comparisons, Logical operators, [If and else statement, Nested if statement], Early Return, Arithmetic operations, Boolean State Variable |
| Haiku, nível 20 (6 conceitos) | [For loop, While loop], [Array indexing, Array length], Numerical comparisons, [Logical operators, Arithmetic operations], [If and else statement, Nested if statement, Boolean State Variable], Early Return |

### sortaSum (A439, problema 1)

| Origem | KCs |
|---|---|
| Duan, lista do prompt de rotulagem (Tabela 10) | Basic arithmetic operations, Logical operators, If and else if statement, Numerical comparisons |
| Tags humanas | If/Else, Math+-*/, LogicAndNotOr, LogicCompareNum |
| TCC 1 | Range validation with logical operators, Using arithmetic operations in conditionals, Compound boolean expressions with logical operators, Returning values from conditional statements, Method parameter usage in computation |
| Sonnet, candidatos | If and else statement, Numerical comparisons, Logical operators, Basic arithmetic operations, Variable declaration and assignment, Return statements and method return values, Ternary conditional operator, Inclusive range boundary handling |
| Haiku, nível 50 (5 conceitos) | Basic arithmetic operations, Numerical comparisons, If and else statement, [Logical AND operator, Logical OR operator, Ternary operator], Variable assignment |
| Haiku, nível 20 (3 conceitos) | Basic arithmetic operations, Numerical comparisons, [If and else statement, Logical AND operator, Logical OR operator, Ternary operator, Variable assignment] |

## Observações

- Com o prompt do Duan, o Haiku 4.5 gera KCs no estilo dos que o paper publica. No love6, os cinco
  KCs gerados do paper têm um correspondente nos seis conceitos do Haiku no nível 50, que acrescenta a
  declaração de variável. Nos 50 problemas, o Haiku dá 125 nomes únicos, contra 103 do paper e 278
  do TCC 1.
- No nível 50, o mesmo da regra atual, o Haiku dá metade dos conceitos do Sonnet, 12 contra 24 e 25
  no A439 e 22 contra 44 e 50 no A502, e cada problema do A439 fica com 4,6 a 4,8 conceitos, contra
  4,4 das tags humanas.
- As tags humanas, de 7 a 13 por exercício, ficam entre os níveis 50 (12 a 27 conceitos) e 20 (5 a
  11). No nível 20, a maior distância dentro de um grupo vai de 0,75 a 0,92, e os grupos juntam ideias
  diferentes, como o if e else com os operadores lógicos e a declaração de variável no love6. No
  nível 50 ela fica entre 0,46 e 0,52.
- Os pares de conceitos com os mesmos problemas, no nível 50, vão de 3 a 14, contra 1 a 4 das tags
  humanas. No A439 caem para 0 no nível 20, à custa dos grupos misturados.
- No A492, no A494 e no A502, o Haiku gera de 10 a 12 candidatos por problema, e no nível 50 cada
  problema fica com 8,2 a 10,3 conceitos, contra 4,6 a 6,8 das tags humanas. No A439 e no A487 são 6,7
  e 7,4 candidatos, e os conceitos por problema ficam perto das tags humanas.
- Juntar os nomes que diferem só em maiúsculas e minúsculas tirou 17 nomes no A494 e 14 no A502 com
  enunciado, como "For Loop" e "For loop".
- No A502, o Haiku com e sem enunciado deu números parecidos, 22 conceitos com e 24 e 22 sem.
- Somando os cinco exercícios, o Haiku no nível 50 dá 97 conceitos para os 50 problemas, e o paper
  50. Parte da diferença é o agrupamento por exercício (decisão 18), que repete em cada exercício
  conceitos como o if e else. Agrupar os 125 nomes juntos, no mesmo nível, daria 61 grupos.
- As duas execuções do Haiku no A439 deram 25 nomes cada e 12 conceitos no nível 50. O Sonnet deu 90
  e 104 nomes no A502.
