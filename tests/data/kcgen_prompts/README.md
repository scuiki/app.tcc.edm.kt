# kcgen_prompts, o prompt de geração do repositório do Duan

Os textos que o teste do `candidate_generation.py` compara, caractere a caractere, com o prompt que
o app monta. Eles não foram escritos à mão. Saíram da execução do próprio código do
`get_KCs_few_shot()` do `KC_gen.py`, no commit `f75da27` do repositório
[umass-ml4ed/kcgen-kt](https://github.com/umass-ml4ed/kcgen-kt), com a entrada do
`generation_input.json`.

## A entrada

- Os dois exemplos são os do repositório (`KC_gen.py:250-260`), o problema dos sinais de mais e o
  da multa por velocidade, com os KCs que o `extract_baseline_kc()` do repositório tira da planilha
  oficial (`data/prompt_concept.csv`) e a lista do `KC_gen.py:544-547` converte para linguagem
  natural.
- O problema analisado é o sortaSum (A439, problema 1), com o enunciado da planilha oficial e
  duas soluções curtas escritas para o teste, que não vêm da CSEDM.

## Os arquivos

- `generation_system.txt`, o texto de sistema para duas soluções, com Java como linguagem.
- `generation_user_with_statement.txt`, a mensagem do usuário com o enunciado.
- `generation_user_without_statement.txt`, a mesma mensagem sem as duas linhas do enunciado
  (`# Problem:` e o texto), que é a única mudança do app quando o exercício não tem enunciado.

Duas linhas terminam com espaço, como no repositório. São a linha depois do passo 4 no texto de
sistema e a abertura da mensagem do usuário ("...using their solution code. "). Um editor que apaga
o espaço no fim da linha quebra o teste.

Para gerar os arquivos de novo, execute o trecho do `get_KCs_few_shot()` que monta o
`system_content` e o `exam_prompt`, com a entrada do `generation_input.json` e os dois exemplos, e
tire do resultado com enunciado as duas linhas do enunciado para ter o sem enunciado.
