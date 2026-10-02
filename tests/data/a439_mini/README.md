# a439_mini, a fixture sintética

O `a439_mini` é um recorte sintético montado em código pela fixture de mesmo nome, no `conftest.py`
da raiz, com as colunas do dado limpo do `docs/GLOSSARY.md`. Ele não é a CSEDM real e não sai de
nenhum arquivo dela.

## O que ele tem

Três alunos inventados (`S1`, `S2` e `S_long`) em três problemas (1, 2 e 3) do exercício 439. O
recorte traz

- eventos `Run.Program` e `Compile.Error`;
- `score` de 0,0 ou 1,0, com o acerto (`is_correct`) só no `Run.Program` com `score` 1,0;
- horários crescentes por aluno;
- Java curto que o javalang lê, e um trecho quebrado de propósito, para a guarda do parser;
- um problema repetido, para o `is_first_attempt` ter verdadeiro e falso;
- um aluno com 8 eventos (`S_long`), para exercitar o truncamento.

## O que ele não é

- Não é lido do disco nem derivado da CSEDM real.
- Nenhum teste afirma um AUC sobre ele, porque a numérica em dado sintético é arbitrária. A
  checagem em dado real é o teste de regressão (`tests/test_regression_a439.py`, marcador
  `regression`), que lê a CSEDM por `EDMKT_CSEDM_PATH`, treina o A439 com as dez seeds na GPU e
  confere a média do first-attempt AUC em ±0,1 ponto em torno de 0,7278. A comparação com o paper é
  o `tests/test_literature_comparison.py`, marcador `literature`.

Os testes de `src/ml` e `src/api` usam a fixture só para travar formas e comportamento. No `ml/`, a
montagem e o truncamento das sequências, os tensores de entrada e o treino curto em CPU. No `api/`,
a limpeza, a treinabilidade e as estatísticas da importação.
