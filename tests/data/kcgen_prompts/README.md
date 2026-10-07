# kcgen_prompts, os prompts do KCGen-KT do Duan

Os textos que os testes do `candidate_generation.py` e do `group_naming.py` comparam, caractere a
caractere, com os prompts que o app monta. Os da geração não foram escritos à mão. Saíram da
execução do próprio código do `get_KCs_few_shot()` do `KC_gen.py`, no commit `f75da27` do
repositório [umass-ml4ed/kcgen-kt](https://github.com/umass-ml4ed/kcgen-kt), com a entrada do
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

## A nomeação dos grupos

O prompt da nomeação vem da Tabela 10 do paper (p. 33422), e não do repositório, que muda palavras
dela. O PDF é texto diagramado e não guarda os recuos, os espaços em sequência nem todas as quebras
de linha, então o `naming_system.txt` tem as palavras da tabela na disposição de linhas do
`KC_cluster_summarize()` do `KC_gen.py`. Sem contar espaços e quebras de linha, ele tem as mesmas
225 palavras do texto de sistema da tabela, na mesma ordem.

- `naming_input.json`, a lista do exemplo da Tabela 10.
- `naming_system.txt`, o texto de sistema.
- `naming_user.txt`, a mensagem do usuário, com a lista em JSON, no formato que o texto de sistema
  anuncia, como o repositório faz com `json.dumps`.

## Os prompts do app

Os textos de sistema dos dois pedidos que o app acrescenta ao método, os trechos de cada conceito e a
tradução, que não vêm do Duan. Eles seguem o formato dos prompts dele, com os passos e o modelo de
JSON, e foram aprovados pelo Leo em 06/10/2026. Os testes do `evidence_location.py` e do
`text_translation.py` comparam o texto do app com eles, para uma mudança no prompt ser deliberada.

- `evidence_system.txt`, o texto de sistema do pedido dos trechos.
- `translation_system.txt`, o texto de sistema do pedido da tradução.
