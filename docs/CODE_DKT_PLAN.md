# Plano de implementação do Code-DKT

O plano que leva ao código as decisões do Code-DKT registradas no `DEVELOPMENT.md`. Aprovado pelo
Leo em 01/10/2026. As decisões e o porquê de cada uma estão no `DEVELOPMENT.md`, e este documento
diz como e em que ordem elas entram no código.

## Escopo

Entram as decisões que mudam o código, as linhas 1, 2, 3, 6, 7, 9, 13, 15, 16, 17, 18, 19 e 21 do
`DEVELOPMENT.md`. As linhas 4, 5, 8, 10, 11, 12, 14 e 20 já estão no código e não mudam.

Ficam de fora o KCGen-KT (Duan), que vem depois deste plano, a importação da turma nova e o
retreino no app, que vêm depois do Duan, a remoção da turma antiga e o push. A turma nova é
importada, extraída e treinada uma vez só, com os dois métodos prontos. Até lá, o A439 da turma
antiga continua servindo o modelo v5 pela matriz de domínio já gravada.

## Decisões fechadas com o Leo

- **A, vocabulário (linha 21).** Conta todos os paths das soluções de treino, como o repositório
  (critério 3).
- **B, viés do W_0 (linha 6).** Sem viés, `nn.Linear(2M + 300, 2M + 300, bias=False)`, como a equação
  e o texto do paper (critério 1).
- **C, artefatos antigos.** O `config.json` do artefato ganha a chave `format_version`, e o artefato
  sem a versão atual é recusado com o `IncompatibleTrainedModelError`, uma resposta 409 com mensagem
  clara. A matriz de domínio já gravada do v5 continua servindo o painel.
- **D, perda na tela.** A curva de perda mostra a perda média por aluno, a soma da época dividida
  pelos alunos que entraram na perda, os que têm ao menos uma previsão válida. O treino não muda.
- **E, faixa do teste de regressão.** A largura é decidida com o Leo depois de medir a repetição das
  execuções na etapa 5.
- **F, comparação com o paper.** Um teste à parte, `tests/test_literature_comparison.py`, com o
  marcador `literature`, fora da suíte padrão. Ele só roda os cinco exercícios e imprime a tabela,
  com `-s`, sem nenhuma asserção contra os números do paper. Falha só por erro de execução ou por AUC
  indefinido.
- **G, aviso da importação.** Conta todo aluno com `Run.Program`, como a partição.
- **H, VRAM.** Só se o R=100 não couber na GPU com lote 128. Nesse caso, parar e decidir com o Leo o
  acúmulo do gradiente em pedaços do lote, que dá o mesmo gradiente esperado com numérica diferente,
  antes de medir o centro da faixa. Se for usado, entra na justificativa e no Estado da linha 14 do
  `DEVELOPMENT.md` como decisão do app (critério 5), o porquê vai para o `DECISIONS.md` e o nome do
  tamanho do pedaço entra no `GLOSSARY.md` antes do código.
- **I, GPU.** A api fica parada durante as execuções longas na GPU, a medida de VRAM e a etapa 5, e
  nenhuma execução na GPU começa com treino ou extração rodando, porque o teste roda fora do
  `OneJobAtATimeLock`.
- **Perda (linha 16).** Vem do repositório só a agregação, a média de cada aluno somada no lote. As
  previsões continuam as do app, todas a partir do histórico, sem a previsão da primeira execução a
  partir das posições vazias (linha 12). O aluno sem previsão válida fica fora, sem NaN, e a perda usa
  só operações densas, sem `index_add_` nem `scatter_add_`, para não perder a repetição na GPU.

## Etapas

Cada etapa é um commit, com uma revisão independente do diff contra as decisões antes de commitar.

### 0. Registro e nomes, antes do código

- `DEVELOPMENT.md`. A linha 21 com a decisão A, na tabela, na justificativa e no Estado. Na
  justificativa 6, o B e a posição do `code_vector_layer` no `__init__`, depois das camadas da atenção
  e antes do LSTM, que muda o consumo do RNG na inicialização. Na justificativa 16, o detalhe da
  perda, sem tocar no texto da linha 12. Em Fontes, uma frase dizendo que as linhas do app citadas
  são do commit `eb95fa0`.
- `DECISIONS.md`. O porquê de C, D, F e G.
- `CLAUDE.md` e a regra de trabalho do `IMPLEMENTATION_PLAN.md`. A restrição do Code-DKT passa a
  apontar para o `DEVELOPMENT.md`, com as decisões em implementação por este plano.
- `IMPLEMENTATION_PLAN.md`. As decisões da discussão da seção 7 e a ordem nova, com este plano.
- `GLOSSARY.md`. Os nomes novos e os que mudam de sentido, na seção Pipeline de dados.

### 1. Ambiente (linha 2)

- `PYTHONHASHSEED=0` no `./Dockerfile`, a base que a imagem do app herda, com o cabeçalho dele
  atualizado.
- A sequência de imagens é `docker tag edmkt-core:dev edmkt-core:pre-hashseed`,
  `docker build -t edmkt-core:dev .`, `docker compose build api` e `docker compose up -d api`. No
  processo vivo, `docker compose exec api python -c "import sys; print(sys.flags.hash_randomization)"`
  tem de dar 0.
- Um teste-guarda em `src/ml/code_dkt/ast_paths_test.py`, e a mesma checagem no carregador da CSEDM
  do teste de regressão, falhando alto em vez de pular.
- Rodar o teste de regressão de hoje uma vez. Com a partição do TCC 1 (`min_attempts=3`, 410 alunos,
  `random_state=1`), `strict=False`, na GPU e com o hash 0, ele deu 0,7595 em 24/09/2026, pela nota
  de memória dessa data. O commit `d3cc9f8` só registra a alternância entre 0,7595 e 0,7608. Se der
  0,7608, o ENV não chegou ao processo. Se der outro valor, comparar o `pip freeze` das duas imagens
  com o `requirements.lock` antes de seguir. Registrar o valor na linha 2 do `DEVELOPMENT.md` e
  capturar o `pip freeze` novo.

### 2. Dados (linhas 9 e 13)

- A partição recebe o exercício e monta a lista com `pd.unique` dos alunos que têm `Run.Program` no
  exercício, na ordem das linhas, sem filtro, com `train_test_split(test_size=0.2, random_state=1)`.
  O caminho de um DataFrame só do `train_and_evaluate` passa a filtrar o exercício. Teste com um
  `Compile.Error` de outro aluno antes do primeiro `Run.Program`.
- O teste de regressão divide por exercício e confere, sem treinar, que os alunos de teste do A439
  são os mesmos do procedimento literal do `src/preprocessing.py` do repositório sobre o mesmo
  `MainTable.csv`, com 386 alunos e 78 no teste.
- Um teste de ponta a ponta da ordem do arquivo até o banco, em
  `import_classroom_dataset_use_case_test.py`, com a fixture `import_classroom`.
- O aviso da importação (G), no `trainability_check` e no teste dele.
- Regressão de uma seed no fim, de 1 a 2 minutos, com o AUC na mensagem do commit.

### 3. Paths, vocabulário e formato (linhas 1, 3 e 21, e C)

- Primeiro, medir a VRAM com R=100, lote 128 e o vocabulário de A, num passo de treino e no forward
  da avaliação, pelo `nvidia-smi`, com o monitor ligado e a api parada. Se não couber, parar e decidir
  o H. Registrar o número no Estado da linha 1.
- O cache guarda todos os paths de cada solução, num diretório com a `AST_PATH_CACHE_VERSION`, em
  `data_layout.ast_path_cache_dir`. O cache antigo, de dono root em `/srv`, fica ignorado, sem apagar
  nada. O `java_parse_rate` e o `ast_path_cache` deixam de passar R e seed ao extrator.
- O sorteio vira uma função só, `sample_ast_paths()`, com
  `random.Random(path_sampling_seed).sample(paths, 100)` por solução, só quando a solução tem mais
  de 100 paths. Treino, avaliação e inferência usam essa função. Um teste confere que a mesma
  solução dá a mesma amostra em qualquer ordem e em qualquer divisão em pedaços, e que a amostra é a
  mesma que o `extract_ast_paths` de hoje sortearia com R=100.
- O vocabulário conta todos os paths do treino (A), com `PADDING_INDEX` igual a 0, `UNKNOWN_INDEX`
  igual a 1 e os tokens reais a partir de 2.
- O `train_and_evaluate` recebe os paths já extraídos. O `MlCodeDktTrainer` passa o que leu do
  cache, e a regressão e o `evaluate_over_seeds` extraem uma vez no `ml/`.
- A marca de formato no `config.json` e a recusa (C), com o erro em `shared/domain/errors` e o
  mapeamento em `error_handlers.py`, e a lista dos erros do domínio no `ARCHITECTURE.md`.
- A inferência (`predict_current_state`) e a avaliação (`predict_code_dkt`) em pedaços de
  `INFERENCE_CHUNK_SIZE` alunos, para a memória não estourar com R=100.
- Fixtures e testes que mudam. São o `cache_config`, o `tiny_vocab` (tokens reais a partir de 2, sem
  as sentinelas no dicionário), o `training_inputs`, o `ast_path_cache_test`, o `java_parse_rate_test`,
  o `model_input_test`, o `student_split_test`, o `train_and_evaluate_test` e o `ast_paths_test`.
  Testes novos para o cache antigo ignorado e para o artefato sem a marca recusado.
- Um teste de que a montagem da entrada usa o `sample_ast_paths()`, e não os 100 primeiros, no treino,
  na avaliação e na inferência.
- Regressão de uma seed, com o AUC na mensagem do commit, e contagens de sanidade (386 alunos, 78 no
  teste, paths por solução até 100, fração de desconhecidos no teste).

### 4. Rede e treino (linhas 6, 7, 15, 16 e 17)

- O `code_vector_layer`, o W_0 quadrado do tamanho de e_r, sem viés (B), na posição registrada na
  justificativa 6.
- Sem dropout na saída do LSTM. O parâmetro sai do modelo, de `CODE_DKT_HYPERPARAMETERS`, de
  `training.py`, de `trained_model_file_store.py` e das fixtures (`tiny_config`, `trained_artifact`,
  `trained_model_file_store_test` e o `training_inputs` de `src/ml/code_dkt/conftest.py`).
- Sem corte de gradiente. Sai o `clip_grad_norm_` de `training.py` e a chave `grad_clip`.
- A `TRAINED_MODEL_FORMAT_VERSION` sobe junto com o W_0 e a saída do dropout, com um teste de que o
  artefato com a versão da etapa 3 é recusado com o `IncompatibleTrainedModelError`.
- A perda conforme as decisões fechadas, com um `loss_test` que trava três coisas. A primeira
  execução nunca vira alvo, um aluno de uma execução não dá NaN, e a agregação é a média de cada
  aluno somada no lote.
- O cuDNN determinístico também na GPU, com o `random_seed_test` conferindo isso no modo não estrito.
  O comentário de `ml_code_dkt_trainer.py` sobre a banda de ±3pp é reescrito junto.
- A perda mostrada na tela (D), no `TrainingEpochMetric` e no `run_training_use_case`.
- Regressão de uma seed no fim, com o AUC na mensagem do commit.

### 5. Avaliação e comparação (linhas 17, 18 e 19)

- `evaluate_over_seeds`, em `src/ml/evaluation/seed_evaluation.py`, com as `EVALUATION_SEEDS`. Ele
  devolve um `SeedEvaluation` e falha com mensagem clara se alguma seed der AUC indefinido, com um
  teste de um caso de classe única.
- O carregador da CSEDM vai para `tests/fixtures`, registrado em `pytest_plugins` e parametrizado
  pelo exercício. O marcador `literature` é registrado em `markers`, e o `-m` do `addopts` passa a
  `'not regression and not literature'`, com o `--import-mode=importlib` mantido. A exceção entra no
  `ARCHITECTURE.md`, no `pyproject.toml` e no README no mesmo commit, com o comando usando `-s`.
- Rodar as dez seeds do A439 duas vezes, com a api parada, e comparar seed a seed. O resultado vai
  para a linha 17. Se não repetir, voltar ao Leo antes de ligar qualquer coisa além do cuDNN.
- Decidir a largura da faixa (E) com o Leo a partir dessa medida, registrar na justificativa 19 e
  gravar o centro no teste de regressão, que passa a rodar as dez seeds.
- A comparação dos cinco exercícios (F), com a média e o desvio registrados na justificativa 19
  contra as Tabelas 1 e 2. O mapeamento fica registrado lá também. O A1 é o 439, pela Tabela 3 do
  paper e pelo repositório, e o A2 a A5 são o 487, o 492, o 494 e o 502, inferidos da ordem crescente
  dos ids no TCC 1.
- Os AUC de uma seed das etapas 1 a 4 entram no registro, para mostrar o efeito de cada grupo de
  decisões.

### 6. Documentação

- README (números, comando e o multi-seed que vira teste), `ARCHITECTURE.md` (verificação, layout do
  cache com versão, exceção de `tests/`) e `DECISIONS.md` (as entradas de fidelidade passam a apontar
  para o `DEVELOPMENT.md`, a afirmação de que treino e inferência leem o mesmo cache é corrigida e a
  linha que chama o teste de regressão de oráculo científico muda).
- `GLOSSARY.md` (conferência final), `pyproject.toml` (a descrição do marcador `regression` e os
  comentários com o 0,7608 e a banda), `requirements.lock` (cabeçalho e lock recapturado) e
  `tests/data/a439_mini/README.md`.
- Os comentários de `src/ml/code_dkt` e `src/ml/reproducibility` onde a numérica mudou, sem citar
  docs e sem mexer em `src/ml/kc_generation`.
- O `CLAUDE.md` com os valores finais, o Estado do `DEVELOPMENT.md` com o commit de cada linha, o
  estado deste plano e as memórias desatualizadas.

## Verificação

- Os testes rodam no container, o pytest na `edmkt-core:dev` e o Vitest no `web` se a tela mudar,
  junto com o `code_comments_test`, o `architecture_test` e o import-linter. O import-linter tem um
  contrato já quebrado, anterior a este trabalho.
- O teste vem antes do código em cada mudança de comportamento, e os testes que fixam a numérica
  antiga são reescritos na etapa que os quebra.
- Medidas de uma seed nas etapas 1 a 4, a medida de VRAM na 3, e as dez seeds duas vezes mais a
  comparação na 5. Cada treino leva cerca de 1 minuto, as dez seeds duas vezes de 20 a 40 minutos e
  a comparação dos cinco exercícios perto de 1 hora.

## Estado

| Etapa | Estado |
|---|---|
| 0 | Concluída |
| 1 | Concluída |
| 2 | Concluída |
| 3 a 6 | A fazer |
