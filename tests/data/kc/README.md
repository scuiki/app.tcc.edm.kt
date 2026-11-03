# kc, a extração de referência do KCGen-KT no A439

Os artefatos que os testes de regressão do KCGen-KT comparam. Saíram da extração do A439 na turma
"CSEDM CodeWorkout Haiku", feita em 02/11/2026 pelas rotas da API, com o código do commit
`3286761`, o modelo `claude-haiku-4-5-20251001` e a versão `kcgen-v2` dos prompts. O resultado está
em `docs/results/kcgen_kt_a439_reference_extraction.md`. A regressão fica só no A439, como o Leo
decidiu em 07/10/2026.

Os dois arquivos foram exportados do banco do app e do cache da turma, sem mudança, e substituem a
extração de 06/10/2026, feita com o `claude-sonnet-5-5`, que está no histórico do git.

- `a439_llm_cache.json`, o cache das respostas do LLM da extração, com a geração, a nomeação, os
  trechos e a tradução. A chave de cada resposta é a etapa seguida do hash do modelo, da versão do
  prompt, do texto de sistema, do schema e do prompt, então uma mudança em qualquer um deles faz a
  resposta faltar.
- `a439_reference_extraction.json`, o que a extração gravou. São as soluções amostradas de cada
  problema pelo `CodeStateID`, na ordem do prompt, os KCs candidatos de cada problema, com o nome, a
  justificativa e a justificativa traduzida, o grupo de cada nome, os conceitos, com o nome gerado e
  o nome em português, os conceitos de cada problema, que formam a Q-matrix, e os trechos, com a
  solução e as linhas.
