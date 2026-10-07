# Plano de implementação do KCGen-KT

O plano que leva ao código as decisões do KCGen-KT registradas no `DEVELOPMENT.md`. Aprovado pelo
Leo em 04/10/2026. As decisões e o porquê de cada uma estão no `DEVELOPMENT.md`, e este documento
diz como e em que ordem elas entram no código.

## Escopo

Entram as 29 linhas do KCGen-KT no `DEVELOPMENT.md`, os três acréscimos de "O que o app acrescenta
ao KCGen-KT" (os trechos de cada conceito, os nomes e as justificativas em português e os problemas
sem conceito), o arquivo de enunciados na importação, a extração de referência da CSEDM numa turma
nova e a comparação com o paper. A revisão pelo professor já existe e não muda.

Fica de fora a parte visual, que entra com a tela Conceitos. São o enunciado na lista de problemas,
a origem do conceito com as soluções, os trechos destacados e as justificativas, a lista de
problemas sem conceito e as rotas que servem a tela, além do item do arquivo de enunciados na tela
Importar dados. A única mudança na tela neste plano são os textos das duas etapas novas da extração
(decisão K). Também ficam de fora a aprovação dos conceitos e o treino da turma nova, que o Leo faz
depois deste plano, e as turmas antigas, que mantêm os conceitos e as descrições que já têm.

## Decisões fechadas com o Leo

- **A, o nome em inglês.** O `kc` ganha uma coluna com o nome que o método gerou, em inglês e em
  minúsculas (linha 25), e o `name` passa a guardar o nome em português, que a tela mostra e o
  professor renomeia. O conceito que o professor cria fica sem o nome gerado.
- **B, a descrição deduzida.** A extração para de gravar a `problem.description` (linha 11). A
  coluna, a rota e a tela continuam como estão até a tela Conceitos, que troca a descrição pelo
  enunciado e apaga a coluna. As descrições já gravadas das turmas antigas não mudam.
- **C, o enunciado.** É opcional. A importação e a extração funcionam com ou sem ele, e o problema
  sem enunciado é extraído com o prompt sem as duas linhas do enunciado (linha 14). Uma coluna nova,
  `problem.statement`, que pode ser nula, é gravada pela importação quando o pacote traz o arquivo.
  Na etapa de processar o pacote, a importação procura, entre os CSV do zip, o que tem as colunas
  `AssignmentID`, `ProblemID` e `Requirement`, e casa cada linha com o exercício e o problema. O
  arquivo vai dentro do zip, junto da `MainTable.csv` e do `CodeStates.csv`, porque o upload aceita
  um arquivo só.
- **D, o que a extração grava.** Três tabelas novas, gravadas na mesma transação da extração. As
  soluções amostradas de cada problema (`SampledSolution`), com chave estrangeira para o problema e
  para a execução escolhida (`submission.id`), e a posição no prompt. A execução já tem o aluno
  (`student_id`), o horário (`submitted_at`) e o código, e o problema leva ao exercício e à turma,
  então nada disso é repetido. Os KCs candidatos de cada problema, com o nome e a justificativa em
  inglês, a justificativa em português e o conceito em que caíram. Os trechos de cada conceito em
  cada problema, com chave estrangeira para a solução amostrada e as linhas. O `kc_job` ganha o ID
  do modelo e a versão do prompt (linha 9).
- **E, os modelos de vetores na imagem.** O CodeBERT e o SBERT passam a ser baixados no build da
  imagem base, a `edmkt-core:dev`, com a revisão do Hugging Face fixada, para os testes e o app
  usarem os mesmos arquivos. O `transformers`, o `tokenizers`, o `huggingface_hub` e o
  `safetensors` ganham versão fixada no `pyproject.toml` e no `requirements.lock`, a mesma que a
  imagem já tem, para o SBERT não mudar.
- **F, o CodeBERT na GPU.** A extração e o treino nunca rodam juntos, porque o
  `OneJobAtATimeLock` serializa os dois, então o CodeBERT usa sempre a GPU quando ela existe, para a
  extração sair mais rápido, mesmo que os vetores variem um pouco entre execuções. A medida da
  etapa 1 registra o tempo e se duas execuções dão os mesmos vetores.
- **G, a resposta inválida.** A resposta do LLM é validada antes de ir para o cache, e uma resposta
  inválida nunca fica guardada (linha 17). Ela é pedida até 3 vezes ao todo, como o erro
  transitório, e depois a extração para com erro.
- **H, os prompts que não vêm do Duan.** O texto dos dois prompts novos, o dos trechos e o da
  tradução, é mostrado ao Leo na etapa 6, antes do commit e antes de qualquer chamada real.
- **I, a ordem da extração de referência.** O A439 primeiro, com uma parada para o Leo ver o número
  de conceitos e o resultado (linha 19), e depois os outros quatro exercícios. Em 07/10/2026, depois
  de ver o A439, o Leo decidiu que a extração de referência fica só nele, e que os outros quatro
  saem pela aplicação, como o professor faria.
- **J, quem dispara.** As chamadas reais ao LLM gastam cota da assinatura, e o Leo autorizou, em
  04/10/2026, que elas sejam disparadas sem ele. As de validação das etapas 4 a 6, uma por prompt
  num problema do A439, e duas no de geração, com e sem enunciado, saem de um script fora do
  repositório. A extração de referência da etapa 7 sai pelas mesmas rotas da API que a tela usa. Os
  testes usam LLMs falsos.
- **K, os estágios novos na tela.** A extração ganha os estágios `evidence` e `translate`, depois de
  `qmatrix`, e o diálogo de extração ganha os dois textos, "Apontando onde cada conceito aparece nas
  soluções" e "Traduzindo os conceitos para o português". Um estágio que a tela não conhece faz o
  diálogo parecer parado até o fim. A amostragem com o CodeBERT continua dentro do estágio
  `generate`.

## Etapas

Cada etapa é um commit, com uma revisão independente do diff contra as decisões antes de commitar.

### 0. Registro e nomes, antes do código

- Este plano vira `docs/KCGEN_KT_PLAN.md`, e o Estado do `DEVELOPMENT.md` passa a apontar para ele.
- `GLOSSARY.md`. Os nomes novos, que são o enunciado, o arquivo de enunciados, o KC candidato com a
  justificativa, o nome gerado do conceito, o trecho do conceito, a proporção do nível de abstração,
  os modelos de vetores e os estágios `evidence` e `translate`. O `SampledSolution` muda de sentido,
  passando a ser uma solução por grupo do CodeBERT. Saem a faixa de tentativas, o silhouette e a
  descrição deduzida pelo LLM.
- `DECISIONS.md`. O porquê das decisões de engenharia, de A a H e K, e as entradas que mudam, a
  ordem dos problemas (`:105-107`), a descrição (`:221-224`), os prompts congelados e a chave do
  cache (`:116-122`), o Haiku (`:124-127`), as etapas (`:150-152`) e a origem do conceito
  (`:615-621`).
- `CLAUDE.md`. O Sonnet 5.5 no lugar do Haiku, o CodeBERT e o `transformers` na tabela do stack, a
  proporção do paper no lugar do silhouette, e a restrição de fidelidade estendida ao KCGen-KT,
  apontando para o `DEVELOPMENT.md`.
- `IMPLEMENTATION_PLAN.md`. O B1 passa a apontar para este plano, a pendência do A439 sem descrição
  sai e a ordem nova cita o plano.

### 1. Ambiente (E e F)

- O download do `microsoft/codebert-base` e do `all-MiniLM-L6-v2` vai para o `./Dockerfile`, com a
  revisão de cada um fixada, e sai do `deploy/Dockerfile.app`, que herda a base.
- O `transformers`, o `tokenizers`, o `huggingface_hub` e o `safetensors` com a versão do
  `pip freeze` da imagem de hoje, no `pyproject.toml` e no `requirements.lock`, e a conversão
  automática de pesos do `transformers` desligada (`DISABLE_SAFETENSORS_CONVERSION=1`). O
  `pip freeze` da imagem nova é comparado com o lock.
- A sequência de imagens é `docker build -t edmkt-core:dev .`, `docker compose build api` e
  `docker compose up -d api`, sem treino nem extração rodando. No container da api, os dois modelos
  carregam com `HF_HUB_OFFLINE=1`.
- Medir o CodeBERT na GPU, com a api parada, sobre as execuções corretas do A439. Anotar o tempo e
  se duas execuções dão os mesmos vetores, bit a bit (F). O número vai
  para o Estado das linhas 2 e 3. Se os vetores variarem, o teste de regressão da etapa 8 compara as
  soluções sorteadas levando em conta essa variação.

### 2. Enunciados na importação (linha 14 e C)

- A migration `0017` acrescenta `problem.statement`, que pode ser nula. A entidade `Problem` e o
  repositório passam a ler e gravar o enunciado.
- A leitura do arquivo de enunciados entra no leitor do ProgSnap2, no padrão do
  `read_code_snapshots(raw_dir)`. O arquivo é achado pelo cabeçalho, entre os CSV do pacote. O caso
  de uso da importação grava o enunciado de cada problema que casar pelo `AssignmentID` e pelo
  `ProblemID`. A rota de upload não muda.
- Testes. O arquivo é achado pelo cabeçalho, e um CSV sem essas colunas é ignorado. Um pacote sem o
  arquivo importa como hoje, com o enunciado nulo, e um arquivo que só cobre parte dos problemas
  deixa os outros sem enunciado. Um teste de ponta a ponta, com a fixture de importação ganhando um
  zip com o arquivo.

### 3. Amostragem das soluções (linhas 1 a 8 e D)

- No `ml/kc_generation`, os vetores do CodeBERT. O tokenizador corta em 512 tokens, a média da
  última camada usa a máscara de atenção e o resultado é normalizado para norma 1, como o trecho
  comentado do repositório. Roda na GPU quando ela existe (F), em lotes de 32 soluções, porque os
  vetores mudam um pouco com o tamanho do lote.
- A amostragem recebe todas as execuções corretas do problema, em ordem de tempo. Ela usa tantos
  grupos quanto o menor entre 5 e o número de soluções de texto distinto, o
  `AgglomerativeClustering` com distância cosseno e ligação média, e sorteia uma solução por grupo
  com um `Random(42)` novo em cada problema. As faixas de tentativas e os comentários que as
  atribuíam ao Duan saem.
- O gerador recebe o modelo de vetores por injeção, montado no `dependencies.py`, e os testes usam
  um falso.
- A migration `0018` cria a tabela das soluções amostradas, com chave estrangeira para o problema e
  para a execução (`submission.id`) e a posição no prompt, gravada na transação da extração.
- Testes do `ml` com vetores falsos. O número de grupos com menos de 5 soluções distintas, uma
  solução por grupo, o mesmo sorteio para um problema com ou sem os outros problemas e a ordem de
  tempo. Um teste com o CodeBERT de verdade sobre três soluções curtas, com o marcador `regression`.

### 4. Prompt de geração e transporte (linhas 9 a 17, G e D)

- `KC_GENERATION_MODEL_ID` passa a `claude-sonnet-5-5`, e o `PROMPT_VERSION` passa a `kcgen-v2`. A
  chave do cache já lê os dois.
- O `LLMClient` passa a aceitar a chamada sem schema, e o `call_claude` sem schema não passa o
  `--json-schema` e lê o JSON do texto da resposta, como já faz quando falta o `structured_output`.
  O tempo limite da chamada sobe de 120 para 300 segundos.
- O `candidate_generation.py` copia o texto do `KC_gen.py:100-170`, no commit `f75da27`, com o texto
  de sistema, o bloco dos exemplos e a mensagem do usuário. Só troca `{language}` por Java e
  `{len(code_ls)}` pelo número de soluções. Os dois exemplos levam o enunciado e as tags da planilha
  oficial, convertidas pela lista do `KC_gen.py:544-547`. Sem enunciado, só as duas linhas do
  enunciado do problema saem.
- A resposta `{"KC 1": {"reasoning": ..., "name": ...}, ...}` é validada antes do cache (G). Cada
  KC tem nome e justificativa não vazios, e há ao menos um KC.
- A migration `0019` cria a tabela dos KCs candidatos e acrescenta ao `kc_job` o ID do modelo e a
  versão do prompt. O `GeneratedKnowledgeComponents` perde a descrição (B) e ganha os candidatos com
  a justificativa e as soluções amostradas.
- Testes. O prompt montado para uma entrada fixa é igual, caractere a caractere, a um texto de
  referência tirado do `KC_gen.py`, com e sem enunciado, guardado em `tests/data`. Uma resposta
  inválida é pedida de novo e não vai para o cache. O teste da descrição gravada pelo worker sai, e
  o `_EchoLLM` do teste do gerador acompanha o prompt novo.
- Validação real (J). Duas chamadas ao Sonnet 5.5 com o prompt de geração, num problema do A439,
  com e sem o enunciado, por um script fora do repositório e com o cache numa pasta temporária fora
  dele. Confere que a CLI sem schema devolve o JSON no formato do Duan e que a validação o aceita.

### 5. Agrupamento e nomeação (linhas 18 a 26)

- O `kc_grouping.py` calcula o número de grupos pela proporção, o máximo entre 1 e 50/103 dos nomes
  únicos, arredondado. Um nome só vira um grupo sem passar pelo HAC. Saem o silhouette, o
  `CANDIDATE_GROUP_COUNTS`, o `choose_kc_group_count` e o caminho especial de menos de 10 nomes no
  gerador.
- Os problemas entram em ordem numérica, e os nomes de cada problema na ordem da resposta.
- O `group_naming.py` copia o texto da Tabela 10, com a lista em JSON. A resposta tem a
  justificativa, o `representative kc` e o `summary name`, e o nome é o representante ou, se ele for
  nulo, o resumo. O grupo de um KC só fica com o nome do KC, sem chamada. Todo nome vai para
  minúsculas, e os grupos com o mesmo nome viram um conceito só, também na Q-matrix.
- O SBERT também entra por injeção, e a parte de agrupar e nomear ganha testes, o que hoje não tem.
- Testes. A proporção (1, 2, 10, 52 e 103 nomes dão 1, 1, 5, 25 e 50 grupos), o nome só, a ordem
  numérica, o prompt de nomeação igual ao texto de referência da Tabela 10, o grupo de um KC só sem
  chamada, as minúsculas e a fusão. O teste do silhouette sobre os artefatos do TCC 1 sai.
- Validação real (J). Uma chamada de nomeação sobre um grupo dos KCs da validação da etapa 4.

### 6. Trechos, tradução e problemas sem conceito (O que o app acrescenta, H e K)

- O prompt dos trechos é do app, em inglês. Para cada problema, ele recebe as soluções amostradas
  numeradas e os conceitos finais do problema, e devolve, para cada conceito, a solução e o trecho
  copiado dela. O app procura o trecho na solução, guarda as linhas e descarta o trecho que não
  acha. Uma chamada por problema, em paralelo, com a etapa de cache `evidence`.
- O prompt da tradução é do app. Uma chamada por exercício recebe os nomes finais e as
  justificativas dos KCs candidatos e devolve o português de cada um, mantendo os termos de Java
  como estão. A validação confere que todo item voltou traduzido. A etapa de cache é `translate`.
- Os textos dos dois prompts são mostrados ao Leo antes do commit (H), e depois de aprovados passam
  pela validação real (J), uma chamada de cada sobre o problema da validação da etapa 4.
- A migration `0020` acrescenta o nome gerado ao `kc` (A) e cria a tabela dos trechos, com chave
  estrangeira para a solução amostrada. O `kc.name` recebe o nome em português.
- O gerador emite os estágios `evidence` e `translate`, e o `GENERATION_STAGES` do front ganha os
  dois textos de K, com os testes do Vitest. O `DESIGN.md` e a página do design ganham os textos, e
  os comentários que listam três estágios (`kc_generation_job_entity.py` e
  `get_kc_generation_job_dto.py`) passam a listar os cinco.
- Um problema sem execução correta não para a extração. Ele fica sem soluções amostradas e sem
  conceito, e um teste garante isso. A lista para o professor sai desses dados, na tela Conceitos.

### 7. Extração de referência da CSEDM (linhas 14, 19 e 28, I e J)

- A turma nova é criada pela API, com o zip da variante CodeWorkout e a planilha oficial dentro
  dele, e a importação passa pelas mesmas rotas que a tela usa. Uma consulta só de leitura confere
  que os 50 problemas ganharam enunciado.
- A extração do A439 é disparada pela rota da extração e acompanhada pelo job (J). O Leo vê o
  número de KCs candidatos por problema, de nomes únicos, de grupos e de conceitos, os trechos
  descartados, o tempo e o número de chamadas, e aprova antes de seguir. Os números do paper, 103
  nomes para 50 problemas, servem de orientação (linha 19).
- Os outros quatro exercícios saem depois, pela aplicação (I).
- Os números vão para o Estado das linhas 19 e 28, e o resultado do A439 está em
  `docs/results/kcgen_kt_a439_reference_extraction.md`, com os trechos e o código das soluções em
  `docs/results/kcgen_kt_a439_evidence.md`.

### 8. Testes de regressão (linhas 27 e 28)

- Os artefatos da extração de referência do A439 vão para `tests/data/kc`, no lugar dos do TCC 1.
  São o cache das respostas do LLM, as soluções amostradas, os nomes candidatos, os grupos, os
  conceitos, a Q-matrix, os trechos e as traduções. A planilha oficial também entra em
  `tests/data`, com a origem anotada. A regressão fica só no A439, como o Leo decidiu em 07/10/2026.
- A primeira camada, com o marcador `regression`, porque precisa da CSEDM e dos modelos. O sorteio
  do A439 pelo CodeBERT dá os mesmos `code_snapshot_id`, e o agrupamento dos nomes gravados pelo
  SBERT dá os mesmos grupos.
- A segunda camada, também com o marcador `regression`. A extração inteira do A439, lendo o cache
  gravado com um LLM falso que falha a qualquer pergunta fora dele, dá os mesmos conceitos, nomes,
  Q-matrix, trechos e traduções. A Q-matrix também é conferida na suíte padrão, sem modelos.
- Os testes com os artefatos do TCC 1 saem, e o `kc_reference_dir` aponta para os novos.

### 9. Comparação com o paper (linha 29)

- Uma planilha de anotação do A439, em `docs/results`, com os 10 problemas, os conceitos gerados de
  cada um em inglês, as 18 tags humanas da planilha oficial e as colunas da rubrica do Apêndice F,
  a interpretabilidade de cada conceito, a relevância de cada vínculo e a cobertura de cada
  problema. O problema 13 vai marcado.
- O Leo anota.
- O relatório, em `docs/results`, com a interpretabilidade, a precisão e a cobertura do A439 ao lado
  dos números do paper, e os conceitos do love6 (Tabela 1) e do has77 (Tabela 7) lado a lado. Os
  quatro KCs do sortaSum (Tabela 11) entram à parte, com a ressalva de que o paper não diz se são os
  gerados. Não passa nem falha.

### 10. Documentação

- README (o KCGen-KT deixa de ser dito portado do TCC 1), `ARCHITECTURE.md` (as tabelas novas, os
  modelos na imagem, o comando dos testes de regressão e a linha da descrição que o LLM deduzia),
  `DECISIONS.md`, `GLOSSARY.md` (conferência final), `CLAUDE.md` com os valores finais, o Estado do
  `DEVELOPMENT.md` com o commit de cada linha e o estado deste plano.

## Verificação

- Os testes rodam no container, o pytest na `edmkt-core:dev` e o Vitest no `web` na etapa 6, junto
  com o `code_comments_test`, o `architecture_test` e o import-linter, que tem um contrato quebrado
  anterior a este trabalho.
- O teste vem antes do código em cada mudança de comportamento.
- As chamadas reais ao LLM são só as de validação das etapas 4 a 6, perto de 5 chamadas, e a
  extração de referência da etapa 7, perto de 30 a 40 chamadas por exercício, entre a geração, a
  nomeação, os trechos e a tradução. Ela ficou só no A439, com 33 respostas guardadas.
- O Leo aprova antes de seguir em três pontos, os prompts novos (H), o resultado do A439 (I) e
  qualquer surpresa na extração.

## Estado

| Etapa | Estado |
|---|---|
| 0 | Concluída, commit `29636e9` |
| 1 | Concluída, commit `7dfae7a` |
| 2 | Concluída, commit `0aac582` |
| 3 | Concluída, commit `af49b24` |
| 4 | Concluída, commit `c38eade` |
| 5 | Concluída, commit `11aea49` |
| 6 | Concluída, commit `b5278ac`. Os dois prompts foram aprovados pelo Leo em 06/10/2026, e ele autorizou as chamadas de validação antes disso, em 04/10/2026 |
| 7 | Concluída em 06/10/2026, só com o A439, commits `dbe8fad` e `4edcb3e` (resultado e trechos) |
| 8 | Concluída |
| 9 | A fazer |
| 10 | A fazer |
