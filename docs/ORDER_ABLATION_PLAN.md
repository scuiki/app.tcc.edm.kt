# Plano da ablação da ordem das tentativas no Code-DKT

Documento temporário. Sai do repositório quando a decisão sobre a ordem das execuções for registrada
no `DEVELOPMENT.md`.

## Objetivo

Medir quanto da diferença entre o AUC do app e o de Shi et al. (2022) vem da ordem em que as
tentativas de cada aluno entram no modelo. A ablação não muda o método do app. O padrão continua a
ordem do tempo, e o treino pela tela e o teste de regressão ficam como estão.

## A diferença medida

| | Paper | Repositório | App hoje | Ablação |
|---|---|---|---|---|
| Ordem das tentativas | as últimas 50, "the latest" (p. 55), o que pressupõe a ordem do tempo | a do arquivo (`src/preprocessing.py:22`), que na CSEDM vem em blocos por problema | a do tempo, por `submitted_at` (`src/ml/code_dkt/student_sequences.py:12`) | a do arquivo, como o repositório |
| Primeira tentativa | a primeira em cada problema (p. 56) | o começo de cada trecho seguido do mesmo problema, na janela de 50 (`src/evaluation.py:42`) | a primeira de cada problema na sequência inteira | a mesma do app, que na ordem do arquivo coincide com a do paper |

Nas duas ordens o LSTM lê uma tentativa por vez e cada previsão usa só as anteriores da sequência. O
que muda é a sequência. Na ordem do arquivo o aluno faz todas as tentativas de um problema e depois
todas as do seguinte, na ordem 234, 13, 12, 232, 233, 5, 235, 236, 1 e 3 no A439. Na ordem do tempo
as tentativas de problemas diferentes se intercalam como o aluno as fez.

## O que o dado mostrou antes de medir

Conferido em 18/10/2026 no `MainTable.csv` da CSEDM, só com os `Run.Program`.

- Nos cinco exercícios, cada par de aluno e problema forma exatamente um trecho contíguo no
  arquivo. No A439 são 3.686 trechos para 3.686 pares.
- Dentro de cada trecho as tentativas estão na ordem do tempo, salvo 2 trechos no A439 e 1 no A487.
- No A439, 86 alunos têm mais de 50 execuções, e em 79 deles a janela das últimas 50 começa no meio
  de um trecho.

Por isso, na ordem do arquivo, a primeira tentativa do app (a primeira do par na sequência inteira)
é o começo de cada trecho, igual à do paper e à do repositório. A única diferença que sobra é do
repositório. Quando o aluno passa de 50 execuções, ele conta como primeira a primeira previsão da
janela, mesmo no meio de um trecho, um efeito ligado à previsão da primeira execução a partir do
padding, que o app não faz. Fica fora desta rodada.

## Variantes

| Variante | Ordem | Primeira tentativa | Papel |
|---|---|---|---|
| V0 | tempo | a primeira do par na sequência inteira | o app de hoje, com os números do `code_dkt_literature_comparison.json` e sem treinar de novo |
| V1 | arquivo | a primeira do par na sequência inteira | o efeito da ordem |
| V2 | blocos por aluno, na ordem em que ele começou cada problema, e o `submitted_at` dentro do bloco | a primeira do par na sequência inteira, o começo de cada bloco | os blocos sem a ordem global do arquivo, só no A439 |

O AUC geral não depende da definição de primeira tentativa, então a diferença entre V0 e V1 no AUC
geral é o efeito da ordem sozinho.

A expectativa registrada antes de medir é que a V1 suba o AUC geral, porque dentro de um trecho a
próxima tentativa é sempre do mesmo problema, e que a primeira tentativa suba menos, porque é
prevista depois do trecho inteiro do problema anterior.

A V2 entrou em 19/10/2026, depois da decisão de seguir a ordem em blocos do repositório. Na CSEDM
a ordem global dos blocos difere da ordem em que o aluno começou os problemas em 368 dos 386 alunos
do A439, e 268 deles nunca voltam a um problema depois de começar outro, caso em que a V2 dá a mesma
sequência da ordem do tempo. A expectativa registrada antes de medir é que a V2 fique perto da V0.

## Mudanças no código


1. **Glossário.** Entram no `GLOSSARY.md`, antes do código, a `attempt_order` (`"time"` ou
   `"file"`) e o marcador `ablation`.
2. **`build_student_sequences`.** Ganha `attempt_order="time"`. Com `"time"` ordena por aluno e
   `submitted_at`, como hoje. Com `"file"` ordena só por aluno, de forma estável, e mantém a ordem das
   linhas dentro de cada aluno. A marca de primeira tentativa continua a mesma nas duas. O teste ao
   lado confere as duas ordens com tentativas intercaladas e que o padrão não mudou.
3. **`train_and_evaluate`.** Lê `config.get("attempt_order", "time")` e passa às duas chamadas de
   `build_student_sequences`. O `CODE_DKT_HYPERPARAMETERS` e o worker de treino não mudam.
4. **V2.** A `attempt_order` ganha o valor `"student_blocks"`, que ordena por aluno, pelo momento da
   primeira tentativa dele em cada problema, pelo id do problema no empate e pelo `submitted_at`. O
   teste da ablação roda por exercício e por ordem, e o JSON guarda cada ordem separada.
5. **`tests/test_code_dkt_order_ablation.py`.** Com o marcador `ablation`, fora da suíte padrão
   pelo `addopts`. Roda `evaluate_over_seeds` com `attempt_order="file"` nas dez seeds, grava em
   `docs/results/code_dkt_order_ablation.json` no formato da comparação com o paper e imprime a V0,
   a V1 e o paper lado a lado.

## Execução

Sem rebuild, com a `edmkt-core:dev` atual.

1. A suíte padrão, o lint e o `import-linter` no container.
2. `docker compose stop api`, porque o treino longo na GPU roda com a api parada. O `web` fica no ar.
3. O teste de regressão no A439, que tem que dar de novo a média de 0,7278 e prova que o padrão não
   mudou. Cerca de 4 minutos.
4. A ablação só no A439 (`-k 439`), cerca de 4 minutos. Os outros quatro exercícios rodam depois,
   se o resultado do A439 pedir.
5. `docker compose up -d api`.

## Fora do escopo

- A previsão da primeira execução a partir do padding e a primeira tentativa literal do
  repositório, candidatas a uma rodada seguinte se a V1 não explicar a diferença.
- O dropout na avaliação, o treino pela tela, o retreino da turma e a seção 5.7 do TCC.
- Qualquer registro no `DEVELOPMENT.md` antes da decisão.

## Estado

| Etapa | Estado |
|---|---|
| Plano | registrado em 18/10/2026 |
| Mudanças no código | aprovadas em 18/10/2026, no commit `2b6dc07` |
| Regressão e ablação no A439 | 18/10/2026. A regressão deu de novo a média de 0,7278. Na ordem do arquivo, a primeira tentativa foi 75,42 ± 1,13 e o geral 71,42 ± 0,72, contra 72,78 ± 0,81 e 69,25 ± 0,86 na ordem do tempo e 75,74 ± 0,69 e 74,31 ± 0,90 no paper. O teste tem 608 primeiras tentativas na ordem do arquivo e 618 na do tempo |
| Outros exercícios | 18/10/2026. No AUC geral, a ordem do arquivo fica abaixo da Tabela 1 nos cinco exercícios, de 0,58 a 3,03 pontos, com média de 2,32, e a ordem do tempo fica de 5,06 abaixo a 0,52 acima, com média de 2,07 abaixo. Na primeira tentativa, a troca de ordem muda a média de 2,92 pontos para baixo (A494) a 2,64 para cima (A439) |
| V2 no A439 | aprovada em 19/10/2026, com este registro como ponto de volta |
