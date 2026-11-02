# Glossário

A linguagem do domínio e o nome que cada termo tem no código. Todo nome de classe, função,
arquivo, rota HTTP e campo JSON sai daqui. Se um conceito novo não cabe em nenhuma linha,
ele entra neste arquivo antes de entrar no código.

Regras gerais:

- Código em **inglês**. Documentação em pt-BR.
- Termos da literatura de EDM ficam como a literatura os chama (*mastery*, *AST path*,
  *first-attempt AUC*): são o vocabulário da banca. A exceção é quando o termo nomeia uma
  estrutura que o sistema não entrega. A *Q-matrix* é uma matriz no `ml/`, mas na aplicação o
  que existe são vínculos entre problema e KC (`ProblemKnowledgeComponent`).
- Nomes de classe escrevem o termo por extenso (`KnowledgeComponent`). A abreviação `kc`
  é aceita em variáveis locais, parâmetros e campos (`kc_id`), nunca em nome de classe.
- Nomes de tabela do SQLite podem continuar abreviados (`kc`, `kc_job`, `problem_kc`). O
  repositório traduz tabela ↔ classe.
- Os nomes do ProgSnap2 (`SubjectID`, `CodeStateID`…) só aparecem no código que lê o CSV
  do professor. Dali em diante, o dado já usa os nomes deste glossário.

## Entidades

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `Classroom` | A turma do professor, dona dos dados enviados | `Turma` |
| `ClassroomSlug` | O nome da turma normalizado, para "Turma 6" e "turma  6" serem o mesmo nome | `TurmaSlug` |
| `ClassroomStatus` (`awaiting_data` / `in_progress` / `trained`) | A situação da turma na tela: sem problemas importados, com dados e sem modelo, com ao menos um modelo publicado. Calculado, nunca gravado | — |
| `Assignment` | O "exercício" da UI, uma lista de problemas (ex.: A439). Unidade de treino: um modelo por assignment | — |
| `progsnap_assignment_id` | O ID do assignment **no dataset** (439). Distinto de `Assignment.id`, o ID do banco | derivado do nome por regex |
| `Problem` / `problem_id` | Um "problema" na UI, um item dentro do assignment, com o enunciado (`statement`), opcional, quando o pacote traz o arquivo de enunciados. A tela Conceitos mostra o enunciado na aba Problemas, no balão do número do problema e na origem do conceito, sem as estrelas, porque vem do pacote do professor. A `description` que o LLM deduzia das soluções não é mais gravada e sai da entidade, do banco e das rotas com a tela Conceitos. A chave é (`assignment_id`, `problem_id`), porque o `ProblemID` do dataset só é único dentro do assignment | `ProblemID` |
| `Student` / `student_id` | O aluno | `SubjectID` |
| `CodeSnapshot` / `code_snapshot_id` | O código Java que o aluno enviou numa tentativa | `CodeStateID` |
| `Submission` | Uma tentativa: aluno + problema + snapshot + nota | — |
| `is_correct` | A tentativa acertou (`score == 1.0`). É o rótulo que o modelo aprende | `correct` |
| `SubmissionEvent` | Se o código rodou (`Run.Program`) ou nem compilou (`Compile.Error`). Os **valores** seguem os do ProgSnap2 | `EventType` |
| `KnowledgeComponent` | Um conceito de programação que um problema exige (ex.: "laço com acumulador"). O `name` é o nome em português, que a tela mostra e o professor renomeia, e o `generated_name` é o nome que a extração gerou, em inglês e em minúsculas, vazio no conceito que o professor cria. O nome gerado não aparece na tela. O `updated_at` é a data da última edição do conceito, e a propriedade `is_generated_by_llm` diz se ele leva as estrelas | `KC` |
| `CandidateKnowledgeComponent` | Um KC que o LLM listou para um problema na extração, com o nome e a justificativa (`reasoning`) em inglês, a justificativa em português (`translated_reasoning`) e o conceito em que caiu. A origem do conceito mostra só a justificativa em português, sob o rótulo "Justificativa do modelo de linguagem". Tabela `candidate_kc` | `kc_raw` (TCC 1) |
| `ProblemKnowledgeComponent` | O vínculo "o problema P exige o KC K". O conjunto dos vínculos de um assignment é o que a literatura chama de Q-matrix. Tabela `problem_kc` | `QMatrixBinding`, tabela `qmatrix` |
| `TrainedModel` | Uma versão treinada do Code-DKT: arquivos em disco + métricas no banco | `ModelArtifact` |
| `published_model_id` | A versão de modelo que o dashboard usa | `current_version_id` |
| `TrainingJob` | Um treino em andamento ou concluído | — |
| `TrainingEpochMetric` | A perda de uma época de um treino, mostrada como a perda média por aluno, a soma da época dividida pelos alunos com ao menos uma previsão válida (a curva de perda é a lista delas) | `training_metric` |
| `KnowledgeComponentGenerationJob` | Uma geração de KCs em andamento ou concluída | `KCJob` |
| `StudentMastery` | A chance prevista de um aluno acertar um problema se tentasse agora, lida do último passo do modelo. Uma por aluno × problema, por versão de modelo | `MasteryPrediction` |

## Interfaces

Todo `Protocol` da `api/` começa com `I` e fica numa pasta `interfaces/` (ver
[ARCHITECTURE](ARCHITECTURE.md#nomes)). Quem implementa fica na infraestrutura.

| Interface | Quem implementa | O que é | Nome antigo |
|---|---|---|---|
| `I<Entidade>Repository` (`IAssignmentRepository`, `IClassroomRepository`, `IProblemRepository`, `ISubmissionRepository`, `IKnowledgeComponentRepository`, `IKnowledgeComponentGenerationJobRepository`, `IProblemKnowledgeComponentRepository`, `ISampledSolutionRepository`, `ICandidateKnowledgeComponentRepository`, `IKnowledgeComponentEvidenceRepository`, `ITrainingJobRepository`, `ITrainedModelRepository`, `ITrainingEpochMetricRepository`, `IStudentMasteryRepository`) | `Sqlite<Entidade>Repository` | Ler e gravar uma entidade | sem o `I` |
| `IProgSnapUploadExtractor` | `ProgSnapZipExtractor` | Extrair o `.zip` enviado e achar as tabelas | `ProgSnapUploadExtractor` |
| `IProgSnapTableReader` | `ProgSnapCsvReader` | Ler as tabelas ProgSnap2 do CSV | `ProgSnapTableReader` |
| `IKnowledgeComponentGenerator` | `KcGenKtGenerator` | Gerar os KCs de um assignment | `KnowledgeComponentGenerator` |
| `ICodeDktTrainer` | `MlCodeDktTrainer` | Treinar o Code-DKT sobre um `TrainingDataset` | `CodeDktTrainer` |
| `ITrainedModelStore` | `TrainedModelFileStore` | Guardar e recarregar os arquivos de um modelo treinado | `TrainedModelStore` |
| `IStudentMasteryPredictor` | `MlStudentMasteryPredictor` | Prever a mastery aluno × KC com um modelo treinado | `StudentMasteryPredictor` |
| `IBusinessRule` | cada `*Rule` | Uma regra que um use case de escrita checa | `BusinessRule` |
| `IUnitOfWork` | `SqliteUnitOfWork` | Gravar tudo junto, ou nada | `UnitOfWork` |
| `IJobLock` / `IAcquiredJobLock` | `OneJobAtATimeLock` | Pegar e soltar a trava de job | `JobLock` / `AcquiredJobLock` |
| `IBackgroundJobLauncher` | `SubprocessJobLauncher` | Disparar um worker em background | `BackgroundJobLauncher` |

## Remoção

| Nome no código | O que é |
|---|---|
| `deleted_at` | A data em que a linha foi removida. Vazia enquanto ela está ativa (ver ARCHITECTURE, Remoção) |
| `remove()` / `remove_all_of()` | Os métodos de repositório que removem, marcando `deleted_at` |

## Estados do assignment

`AssignmentStatus` descreve até onde o assignment chegou. Cada transição tem um único dono.

| Valor | Significado | Quem leva até aqui |
|---|---|---|
| `statistics_only` | Os first-attempts têm uma classe só, então o AUC é indefinido e não dá para treinar. Só o bloco "o que aconteceu" fica disponível | importação (antes `eda_only`) |
| `ready_for_kc_generation` | Tem as duas classes; pode gerar KCs | importação (antes `trainable`) |
| `kc_draft` | KCs gerados pelo LLM, aguardando o professor. A aprovação só passa com todo problema ligado a ao menos um KC | geração de KCs; ou editar KCs já aprovados |
| `kc_approved` | O professor aprovou os KCs; pode treinar. Os KCs continuam editáveis, e a primeira edição, depois do aviso de reabrir, devolve o assignment a `kc_draft` | aprovação |
| `trained` | Existe um modelo publicado. Sem re-treino, os KCs ficam como estão; qualquer edição é recusada por `refuse_edit_after_training()` (`services/knowledge_component_edit.py`) | treino |

Na tela, cada situação aparece numa etiqueta de situação, com o rótulo (`ASSIGNMENT_STATUS_LABEL`) e
o ícone da etapa (`ASSIGNMENT_STATUS_ICON`), que o `assignmentStatusBadge()` junta com o tom, azul
só em `trained`. Os blocos marcam as três situações de conceitos, o cérebro marca `trained`, com o
rótulo "Treinado", e `statistics_only` fica sem ícone. No menu, o exercício leva o ponto de situação
(`STATUS_DOT`) no lugar do ícone, com três modificadores. O `awaiting`, vazio e com a dica
"Aguardando conceitos", vale para `ready_for_kc_generation` e `kc_draft`. O `kc_approved` é meio
preenchido, e o `trained` é azul. `statistics_only` fica sem ponto.

Os jobs (`TrainingJob`, `KnowledgeComponentGenerationJob`) têm os estados `pending`,
`running`, `done` e `failed`. O `updated_at` de um job não é a data de uma edição, como no `kc`. No
`kc_job` ele é o batimento do progresso, regravado a cada estágio e a cada item e no fim, e no
`training_job` é só a hora em que o treino terminou, porque o progresso por época fica no
`TrainingEpochMetric`.

Os estágios do `KnowledgeComponentGenerationJob` são `generate`, `cluster`, `qmatrix`, `evidence` e
`translate`, nessa ordem. Ele informa também o progresso dentro do estágio atual, em
`progress_done` e `progress_total`, quantos itens já terminaram, de quantos (problemas no `generate`
e no `evidence`, grupos na nomeação do `cluster`). Os dois ficam vazios quando o estágio não tem
itens para contar. O job guarda também o modelo de linguagem (`model_id`) e a versão do prompt
(`prompt_version`) da extração, gravados pelo `record_generation_model()` no fim dela. Uma chamada
à CLI espera até `CALL_TIMEOUT_S`, 300 segundos.

## Dashboard

A tela "Análise" de cada exercício entrega o dado, não a interpretação. Duas famílias, nunca na
mesma régua: "o que aconteceu" (contagens das execuções, desde a importação) e "o que o modelo
prevê" (só com modelo publicado). Sem níveis, faixas, recomendações ou cortes.

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `StudentMasteryMatrix` | A matriz `{(student_id, problem_id): mastery}`, o dado nativo do modelo | matriz aluno × KC |
| domínio (`mastery`) | A chance prevista de o aluno acertar um problema se tentasse agora, lida do último passo do Code-DKT. Não é a fração do conceito aprendida. Na tela, sempre com o marcador de cérebro (`GeneratedByML`) e a dica com essa frase | — |
| `aggregate_by_knowledge_component()` | O domínio por conceito, a média dos problemas que o exigem, derivado da matriz na leitura e nunca gravado (`services/mastery_by_knowledge_component.py`) | `aggregate_student_mastery` (em `ml/mastery/`) |
| `mean_and_histogram()` | A média e a distribuição em dez faixas de 10 pontos de uma lista de masteries (`services/mastery_distribution.py`) | `MasteryLevel`, `classify_mastery_level()` |
| `mean_mastery_by_student()` / `weakest_knowledge_components()` | A média do aluno sobre os problemas e os três conceitos em que ele está mais fraco (`services/student_mastery.py`) | `find_students_at_risk()` |
| `ConceptBindings` / `load_concept_bindings()` | Os conceitos ativos do exercício com nome e os vínculos com os problemas nos dois sentidos (`application/services/concept_bindings.py`) | `names_including_removed()` |
| `PublishedModelMastery` | Resolve a versão publicada, calcula a matriz uma vez e a serve do banco nas leituras seguintes | — |
| `ProblemStatistics` | O que aconteceu num problema: taxa de acerto em todas as execuções, mediana de tentativas até completar, alunos que tentaram e que completaram, erros de compilação por execução | `PreTrainingStatistics` (por assignment), EDA |
| `KnowledgeComponentStatistics` | A taxa de acerto de um conceito, somando as execuções dos problemas que o exigem | — |
| `StudentActivity` | O que um aluno fez: problemas completados e tentados, execuções e erros de compilação | — |
| curva de aprendizagem (`LearningCurve`) | A taxa de erro de um conceito em cada oportunidade, com quantos alunos chegaram a cada uma. Para quando menos de 10% da turma chega à oportunidade. Sai das execuções e dos vínculos problema × conceito, sem modelo | — |
| oportunidade (`opportunity`) | Cada execução de um aluno num problema que exige o conceito, contada em ordem por aluno e conceito. A 1ª oportunidade é a primeira execução dele num desses problemas | — |
| completar (`completed`) | Ter ao menos uma execução correta no problema | "fechar" |
| dado estimado (`GeneratedByML`) | O marcador de cérebro antes do rótulo de toda coluna que vem do Code-DKT, com a dica "Dado estimado por aprendizado de máquina" | `EstimatedMark`, badge "previsto" |
| gerado pelo modelo de linguagem (`GeneratedByLLM`) | O marcador de estrelas no que o LLM escreveu, com a dica "Gerado pelo modelo de linguagem". Fica no fim do nome do conceito e do título da origem, antes do rótulo da justificativa traduzida e na aba da solução com o trecho, num tamanho para cada lugar. No nome, aparece só com `is_generated_by_llm`, então some quando o professor renomeia o conceito e não aparece no que ele cria. O enunciado não leva | — |
| linha de fatos (`FactsLine`) | A linha de números abaixo do título de uma tela, com os itens separados por vírgula. Na Análise traz alunos, problemas, conceitos, execuções e a versão do modelo com a data do treino, no lugar da descrição fixa. Na Conceitos traz problemas, conceitos, a data da extração e quantos problemas estão sem conceito, em vermelho quando há algum. No diálogo da origem do conceito diz em quantos problemas o conceito aparece | — |
| recorrência (`recurrence`) | Em quantos problemas do exercício um conceito aparece. Com um só, o valor do conceito é o desse problema, evidência fraca. Na matriz da tela Conceitos fica à direita, como "N de M", e dá a ordem das linhas | cobertura |
| `compute_problem_statistics()` / `compute_knowledge_component_statistics()` / `compute_student_activity()` | Calculam as três contagens acima do dado limpo, sem modelo (`services/submission_statistics_calculation.py`) | `compute_pre_training_statistics()` |
| `first_attempt_auc` | A métrica primária: AUC só sobre as primeiras tentativas. Fica no banco e no teste de regressão; não vai para a tela | `first_auc` |

## Turma

As telas Turmas e Turma resumem o que aconteceu em cada exercício e com cada aluno da turma, sem
modelo, exceto o domínio médio dos exercícios treinados.

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `AssignmentOverview` | O resumo de um exercício na turma: período (primeira e última execução), alunos que participaram, execuções e taxa de acerto | — |
| `ClassroomStudentSummary` | A linha de um aluno na turma: exercícios de que participou, problemas completados dos que tentou, execuções, taxa de acerto, erros de compilação, última atividade e domínio médio nos exercícios treinados | — |
| `DailyRuns` | As execuções da turma por dia, ou por semana acima de cerca de 120 dias, para a figura de execuções por dia | — |
| `ActivityEvent` | Um evento da atividade recente: turma criada, dados importados, conceitos extraídos ou modelo treinado, com onde e quando | — |
| próximo passo | A ação que a situação do exercício pede, mostrada como um botão na tabela de exercícios (extrair conceitos, revisar conceitos, treinar modelo, ver análise) | — |

## Conceitos

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `SampledSolution` | Uma das até cinco soluções corretas que a extração escolheu para o LLM ler num problema, uma por grupo dos vetores do CodeBERT. Gravada na extração, com a execução escolhida (`submission_id`), que traz o aluno, o horário e o código, e a posição no prompt. Tabela `sampled_solution` | — |
| `KnowledgeComponentEvidence` | Um trecho de uma solução amostrada em que o conceito aparece, com a primeira e a última linha. O LLM o aponta depois do agrupamento, na mesma extração, e o app confere que ele existe na solução. É a justificativa que o modelo escreve, e não a causa da extração. Tabela `kc_evidence` | — |
| origem do conceito (`KnowledgeComponentOrigin`) | O diálogo aberto pela lupa do conceito, no front o `KnowledgeComponentOriginDialog`, com uma aba por problema ligado (`ProblemOrigin`). Cada aba tem o enunciado, as justificativas traduzidas dos KCs candidatos do par e as soluções amostradas, com o trecho destacado. O par sem KC candidato é o vínculo que o professor fez, e o par com candidato e sem trecho teve o trecho descartado. O front classifica o painel de cada problema (`ProblemOriginKind`) pela `problemOriginKindOf()`, em `evidence` quando há trecho, `discarded_evidence` quando há justificativa e não há trecho e `teacher_link` quando não há justificativa. Sai da rota `GET /knowledge-components/{kc_id}/origin`, uma chamada por conceito | — |
| problema sem conceito | Um problema sem nenhum conceito ligado. Na extração, é o que não tem nenhuma execução correta, e a extração segue com os outros. A tela Conceitos o marca em vermelho na matriz e na linha de fatos, com o motivo no balão do número, e a aprovação é recusada, na tela e no backend, até ele ganhar um conceito | — |
| `updated_at` do conceito | A data da última edição do conceito pelo professor. Hoje só o renomear grava, e não grava nada quando o nome é o mesmo. Vazia no conceito que ninguém editou. O soft delete grava só o `deleted_at`, e ligar e desligar mexem na `problem_kc`, e não no `kc`. Nos jobs, o `updated_at` tem outro sentido (ver Estados do assignment) | — |
| `is_generated_by_llm` | Se o nome do conceito é o que o modelo gerou e leva as estrelas, com o `generated_name` preenchido e o `updated_at` vazio. Propriedade da entidade `KnowledgeComponent`, calculada e nunca gravada. Uma edição nova do `kc` que não seja do nome pede rever a regra | — |
| `correct_run_count` | Quantas execuções corretas um problema tem, as que a extração lê, na rota da tela Conceitos. Com 0, o balão do problema sem conceito diz que ninguém acertou o problema ainda | — |
| `extracted_at` / `find_latest_done()` | A data da extração do exercício, o `updated_at` do `kc_job` concluído mais recente, que o `find_latest_done()` acha. Nula sem extração concluída. A tela a mostra no fuso do navegador | — |
| matriz (`KnowledgeComponentMatrix`) | A aba Conceitos por problema da tela Conceitos, com os conceitos nas linhas, os problemas nas colunas e uma célula por par, que liga e desliga o vínculo no clique. A ordem das linhas é calculada ao abrir a tela e fica fixa enquanto o professor edita (`stableKnowledgeComponentOrder()`). No código, cada célula ligada continua sendo um `ProblemKnowledgeComponent` | `KnowledgeComponentsCard`, as etiquetas com xis do `ProblemsCard` |
| desfecho do clique (`CellClickOutcome`, `cellClickOutcomeOf()`) | O que o clique numa célula da matriz faz, calculado dos problemas e conceitos que a tela já tem. A célula vazia liga (`link`), e a ligada desliga direto (`unlink`), pede confirmação quando o conceito sairia do exercício (`confirm`) ou é recusada quando o problema ficaria sem conceito (`refused`). A recusa vem antes da confirmação | — |
| edição pendente (`PendingCellEdit`) | O clique que liga ou desliga uma célula e espera o aviso de reabrir, guardado pelos ids do conceito e do problema até o professor seguir ou cancelar | — |
| aba Problemas (`ProblemStatementsTable`) | A segunda aba da tela Conceitos, com o número, o enunciado e quantos conceitos cada problema tem | `ProblemsCard` |
| Novo conceito (`NewKnowledgeComponentDialog`) | O diálogo que cria um conceito do professor, com o nome e ao menos um problema. O conceito nasce sem `generated_name`, logo sem as estrelas. A tela recusa o nome repetido comparando pelo `normalizedName()`, sem acento, sem caixa e sem os espaços das pontas | `AddKnowledgeComponentDialog` |
| aviso de reabrir (`ReopenApprovalDialog`, `ReopenApprovalNotice`) | O aviso da primeira edição de um exercício em `kc_approved`, de que editar reabre todos os conceitos para aprovação. É o diálogo do clique na célula, que guarda o clique como uma `PendingCellEdit`, e uma linha (`ReopenApprovalNotice`) dentro da confirmação de remover e da de tirar o último problema e dentro dos formulários de renomear e do Novo conceito | `kc-editor__notice--approved` |

## Importação

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `n_students_eligible` | Quantos alunos de um exercício têm ao menos uma execução `Run.Program`, os que entram na partição | — |
| `PackageRequirement` | Um requisito do pacote ProgSnap2 (tabela de eventos, código dos alunos, formato ProgSnap2 v6, até 512 MB), conferido depois do envio, atendido ou não | "O que veio no pacote" |
| arquivo de enunciados (`find_problem_statements_file()`, `read_problem_statements()`) | O CSV opcional do pacote com o enunciado de cada problema, achado pelas colunas `AssignmentID`, `ProblemID` e `Requirement` (`PROBLEM_STATEMENT_COLUMNS`), as da planilha oficial da CSEDM, e lido quando o pacote é processado. Um pacote sem ele importa sem enunciados | — |

## Pipeline de dados

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `classroom_import` | Receber o `.zip` ProgSnap2, validar, limpar e persistir | `ingestion` |
| `ClassroomImportReport` / `ImportCheck` | O relatório da importação e cada item dele (fatal, aviso ou de treinabilidade) | `IngestReport` / `ReportItem` |
| `check_assignment_trainability()` | Decide, por assignment, entre `ready_for_kc_generation` e `statistics_only` | `viability` |
| tabela `submission` | O dado limpo de onde tudo lê (`ISubmissionRepository.list_by_assignment()`), com o código Java | Parquet por assignment (`cleaned_submissions.parquet`) |
| `list_correct_runs()` | As execuções corretas de um exercício, com o `submission_id` de cada uma, que a extração de KCs lê para escolher as soluções | — |
| `count_correct_runs_by_problem()` | Quantas execuções corretas cada problema de um exercício tem, com o mesmo filtro do `list_correct_runs()` e só os problemas não nulos, para o `correct_run_count`. O problema sem acerto não volta, e quem chama completa com 0 | — |
| `get_codes()` | O código de cada execução pedida pelo `submission_id`, com o `\r\n` e as tabulações intactos, para as soluções da origem do conceito. Filtra só pelo id, porque a solução amostrada já aponta uma execução correta, e o id que não existe é ignorado | — |
| `TrainingDataset` | O recorte que treino e inferência consomem: só eventos `Run.Program` | `ModelingFrame` |
| `load_training_dataset()` | Monta o `TrainingDataset` de um assignment (`services/training_dataset_loading.py`) | `load_modeling_frame` |
| `TrainingOutcome` | O que um treino devolve: o modelo, o vocabulário, os hiperparâmetros, o first-attempt AUC e o `java_parse_rate` | — |
| `DetectedUpload` | O que o upload encontrou no `.zip`: o diretório cru e as tabelas | — |
| `AstPath` | Um caminho na árvore sintática do Java; é a feature de entrada do Code-DKT (termo do artigo) | paths |
| `AstPathCache` | Todos os paths de cada solução, já extraídos e salvos em disco por snapshot, num diretório com a `AST_PATH_CACHE_VERSION`. A amostragem aleatória dos R paths acontece depois, na montagem da entrada | `features_cache` |
| `AST_PATH_CACHE_VERSION` | A versão do método de extração no diretório do `AstPathCache`. Um cache de outra versão é ignorado | — |
| vocabulário (`vocab`) | O mapa dos nós e dos paths do treino em índices (`token_to_idx` e `path_to_idx`), como no code2vec (Alon et al., 2019). Sai só dos alunos de treino e conta todos os paths das soluções deles | — |
| padding (`PADDING_INDEX`) | O índice 0 dos vocabulários de nós e de paths, que completa uma solução com menos de R paths e faz o padding à esquerda da sequência de quem tem menos de 50 execuções | — |
| token desconhecido (UNK, `UNKNOWN_INDEX`) | O índice 1 dos vocabulários, de um nó ou path que não apareceu no treino. Os tokens reais começam no 2 | índice 0 do OOV |
| `sample_ast_paths()` | A amostragem aleatória dos R paths de uma solução com a `path_sampling_seed`, só quando ela tem mais de R paths, usada no treino, na avaliação e na inferência | — |
| `path_sampling_seed` | A seed da amostragem aleatória dos R paths de cada solução, 42, separada da `seed` do treino para os paths não mudarem de um treino para outro | `seed` |
| `code_vector_layer` | A camada linear sem viés que leva a média ponderada dos paths ao vetor de código z, o W_0 de Shi et al. (2022) | — |
| `INFERENCE_CHUNK_SIZE` | Quantos alunos entram de cada vez num forward da inferência e da avaliação, para a memória não estourar | — |
| acumulação de gradiente (*gradient accumulation*, `batch_chunk_size`) | No treino, o forward e o backward vão em batches de 64 alunos, com o gradiente somado até completar o tamanho do lote (*batch size*), para a memória da GPU não estourar | — |
| `EVALUATION_SEEDS` | As seeds dos dez treinos da avaliação, de 42 a 51 | — |
| `evaluate_over_seeds()` | Treina e avalia um exercício uma vez por seed de `EVALUATION_SEEDS` (`ml/evaluation/seed_evaluation.py`) | multirun do TCC 1 |
| `SeedEvaluation` | O resultado de `evaluate_over_seeds()`, com o first-attempt AUC e o AUC geral de cada seed, e a média e o desvio amostral de cada um | — |
| `TRAINED_MODEL_FORMAT_VERSION` | A versão do formato do artefato de um `TrainedModel`, gravada como `format_version` no `config.json` | — |
| `IncompatibleTrainedModelError` | O erro de quando um artefato não tem a `format_version` atual. Vira 409 | — |
| marcador `regression` | O teste que treina o A439 com as dez seeds e confere a média da primeira tentativa em ±0,1 ponto em torno de 0,7278, `tests/test_regression_a439.py`, fora da suíte padrão. O mesmo marcador separa os testes do KCGen-KT que carregam os modelos de vetores ou a extração de referência da CSEDM | — |
| extração de referência | A extração do A439 da CSEDM, feita em 06/10/2026 numa turma própria, cujas respostas do LLM e cujo resultado ficam em `tests/data/kc` para os testes de regressão do KCGen-KT | — |
| tolerância do teste de regressão (`TOLERANCE`) | O quanto a média do first-attempt AUC das dez seeds pode se afastar da média de referência, ±0,001 (±0,1 ponto). A média de referência (`REGRESSION_CENTER`) é 0,7278, a que o app mediu no A439 em 02/10/2026, e fora da tolerância o teste de regressão falha | — |
| marcador `literature` | O teste que compara o app com as Tabelas 1 e 2 de Shi et al. (2022), `tests/test_literature_comparison.py`, fora da suíte padrão | — |
| ordem das tentativas (`attempt_order`) | A ordem em que as execuções de cada aluno entram na sequência do Code-DKT. `"time"`, o padrão do app, ordena pelo `submitted_at`. `"file"` mantém a ordem das linhas do arquivo, como o repositório oficial, e na CSEDM dá um bloco por problema. `"student_blocks"` junta as tentativas de cada problema num bloco, na ordem em que o aluno começou os problemas, com o `submitted_at` dentro do bloco. Só a ablação usa o `"file"` e o `"student_blocks"` | — |
| marcador `ablation` | O teste que mede o Code-DKT na CSEDM com a `attempt_order` `"file"`, ao lado do app e do paper, `tests/test_code_dkt_order_ablation.py`, fora da suíte padrão | — |
| `java_parse_rate` | A fração dos snapshots que o javalang conseguiu parsear | `parse_rate` |
| `ModelProvenance` | O commit do código e o hash do dado que geraram um modelo | `provenance` |
| `predict_current_state()` | O vetor do último passo do Code-DKT, a chance de acerto de cada aluno em cada problema se tentasse agora (`ml/code_dkt/prediction.py`). `predict_code_dkt()` continua sendo a previsão por tentativa, para o AUC | — |
| `CODE_DKT_HYPERPARAMETERS` | Os hiperparâmetros do Code-DKT decididos no `DEVELOPMENT.md`, com a origem de cada um no paper, no repositório oficial ou no app | `FROZEN_CONFIG` |
| `OneJobAtATimeLock` | A trava persistente que garante um único job pesado por vez (treino, geração de KCs, importação) | `PipelineLock`, `pipeline_lock` |
| `AnotherJobRunning` | O erro de quando a trava já tem dono vivo | `PipelineBusy` |

### Colunas do dado limpo

| Coluna | Coluna do ProgSnap2 |
|---|---|
| `student_id` | `SubjectID` |
| `progsnap_assignment_id` | `AssignmentID` |
| `problem_id` | `ProblemID` |
| `code_snapshot_id` | `CodeStateID` |
| `code` | `Code` |
| `score` | `Score` (contínuo, preservado) |
| `submitted_at` | `ServerTimestamp` |
| `event_type` | `EventType` |
| `is_correct` | — (derivado: `Run.Program` e `score == 1.0`) |

## KCGen-KT (geração de KCs)

| Etapa | Nome no código | O que faz | Nome antigo |
|---|---|---|---|
| 1 | `embed_solutions()` + `select_sample_solutions()` | Calcula os vetores do CodeBERT das execuções corretas de cada problema, na GPU, e escolhe até 5 soluções, uma por grupo | `diversity_sample` |
| 2 | `generate_candidate_kcs()` | Pede ao LLM os KCs que cada problema exige, com o prompt de Duan et al. (2026), com ou sem o enunciado. `parse_candidate_kcs()` lê e valida a resposta, e as execuções corretas chegam pelas colunas `CORRECT_RUN_COLUMNS` | `generate_kcs_for_problem` |
| 3 | `embed_kc_names()` + `kc_group_count()` + `group_similar_kcs()` | Calcula os vetores do SBERT dos nomes de KC, o número de grupos pela proporção do nível médio do paper (`MEDIUM_ABSTRACTION_RATIO`, 50/103) e agrupa os nomes de KC parecidos (SBERT + clustering hierárquico) | `choose_kc_group_count` (silhouette), `select_best_n_clusters`, `_cluster_with_n` |
| 4 | `name_kc_group()` | Pede ao LLM o nome de cada grupo com mais de um KC, pela Tabela 10 do paper, e `parse_group_name()` lê e valida a resposta. O grupo de um KC só fica com o nome dele, e os grupos de mesmo nome viram um conceito só | `label_cluster` |
| 5 | `build_qmatrix()` | Monta a Q-matrix problema × KC | `build_qmatrix` |
| 6 | `locate_kc_evidence()` | Pede ao LLM, por problema, onde cada conceito aparece nas soluções amostradas. `parse_kc_evidence()` lê e valida a resposta, e `find_snippet_lines()` acha as linhas do trecho na solução | — |
| 7 | `translate_kc_texts()` | Pede ao LLM o português dos nomes e das justificativas do exercício, numa chamada só, e `parse_translations()` lê e valida a resposta | — |
| — | `CachedLLMClient` | O LLM com o cache das respostas, guardadas por hash, para não pagar duas vezes. Uma resposta só entra no cache depois de validada | `LLMResponseCache`, `kc_cache` |
| — | `LLMClient` | A interface do LLM que o `ml/` declara e a `api/` implementa | `ports.LLMClient` |
| — | `InvalidLLMResponseError` | Uma resposta do LLM vazia, que não é JSON ou fora do formato pedido. É pedida até 3 vezes ao todo, como o erro transitório | `EmptyContentError` |
| — | `KC_GENERATION_MODEL_ID` / `PROMPT_VERSION` | O modelo de linguagem da extração, `claude-haiku-4-5-20251001`, e a versão dos prompts, os dois na chave do cache e gravados no job | — |
| — | `SBERT_MODEL` / `CODEBERT_MODEL` | Os modelos de vetores, `all-MiniLM-L6-v2` para os nomes de KC e `microsoft/codebert-base` para as soluções, em `ml/kc_generation/embedding_models.py`, com a revisão do Hugging Face fixada em `SBERT_REVISION` e `CODEBERT_REVISION` | — |
| — | `download_embedding_models()` | Põe os dois modelos de vetores no cache do Hugging Face, chamada só no build da imagem base | — |
| — | `SOLUTIONS_PER_PROBLEM` / `SOLUTION_EMBEDDING_BATCH_SIZE` | As 5 soluções por problema do experimento principal do paper, e as 32 soluções que entram de cada vez no CodeBERT, fixas porque os vetores mudam um pouco com o tamanho do lote | — |

## Componentes do front

As peças de `src/web/src/components/` que levam um nome próprio do desenho.

| Nome no código | O que é | Nome antigo |
|---|---|---|
| tabela de dados (`DataTable`) | A tabela comum do app, com rolagem lateral no próprio invólucro, nome à esquerda, números e etiquetas centralizados e botões à direita. O cabeçalho simples é o `ColumnHeader`, e o ordenável é o `SortableHeader`, com a mesma estrutura de marcador, rótulo truncado (`ColumnLabel`, com o texto inteiro no balão) e dica | `.analysis-table`, `.classroom-table` |
| bloco de código (`CodeBlock`) | O código com abas presas ao topo, uma por arquivo, a numeração das linhas e as linhas destacadas, que rola por dentro até o destaque. Recebe os arquivos (`CodeFile`, com a chave, o rótulo e o código da aba, e opcionais o ícone e o marcador) e o destaque (`CodeHighlight`, com o arquivo e a primeira e a última linha). Na origem do conceito, as abas são as soluções que o modelo leu, e o destaque é o trecho | — |
| largo (`size="wide"`) | A variante larga do `Dialog`, de 760px no lugar de 440px, para a origem do conceito, e a do `Tooltip`, de 360px no lugar de 260px, para o balão com o enunciado do problema | — |
| só o identificador (`variant="identifier"`) | A variante das `Tabs` em que cada aba mostra só o identificador, como o número do problema na origem do conceito, com o nome acessível "Problema N", e a fileira rola de lado | — |

## Rotas HTTP

| Rota | O que faz | Rota antiga |
|---|---|---|
| `GET /assignments` | Lista os assignments ativos; com `?classroom_id=…`, só os da turma | igual |
| `GET /assignments/{assignment_id}/problems` | Os problemas do assignment pelo `problem_id`. A descrição sai da resposta com a tela Conceitos, e o front não usa a rota | — |
| `GET /assignments/{assignment_id}/problems/knowledge-components` | Cada problema com o enunciado (`statement`), as execuções corretas (`correct_run_count`) e os KCs que exige, cada um com `is_generated_by_llm`, e a data da extração (`extracted_at`). É o que a tela Conceitos lê para a matriz e a aba Problemas, e a descrição sai da resposta com ela (a lógica é de `knowledge_components`) | — |
| `GET /knowledge-components?assignment_id=…` | Os KCs do assignment, cada um com os `problem_ids` a que se liga | — |
| `POST /knowledge-components/{kc_id}/problems/{problem_id}` | Liga um KC que já existe a mais um problema | — |
| `DELETE /knowledge-components/{kc_id}/problems/{problem_id}` | Tira o KC de um problema só; se ele perder o último, sai junto | — |
| `GET /classrooms` | As turmas, com `problem_count`, `student_count` e `status` | — |
| `POST /classrooms` | Cria uma turma só com o nome (409 para nome repetido) | — |
| `PUT /classrooms/{classroom_id}` | Renomeia a turma | — |
| `DELETE /classrooms/{classroom_id}` | Exclui a turma e os assignments dela (soft delete) | — |
| `POST /classroom-imports` | Recebe o `.zip` de um envio para uma turma que já existe (`classroom_id`) e devolve os arquivos detectados | `POST /ingest` |
| `POST /classroom-imports/process` | Importa a variante escolhida na turma (`classroom_id`) | `POST /ingest/process` |
| `POST /knowledge-components/generation-jobs` | Dispara a geração de KCs | `POST /kc/generate` |
| `GET /knowledge-components/generation-jobs/{job_id}` | Progresso da geração | `GET /kc/jobs/{job_id}` |
| `POST /knowledge-components` | O professor cria um KC, com o nome e ao menos um problema (`problem_ids`); a lista vazia ou ausente dá 422 | `POST /kc` |
| `PUT /knowledge-components/{kc_id}` | Renomeia um KC e grava o `updated_at`; o mesmo nome devolve o KC sem gravar | `PATCH /knowledge-components/{kc_id}` |
| `DELETE /knowledge-components/{kc_id}` | Remove um KC | `DELETE /kc/{kc_id}` |
| `GET /knowledge-components/{kc_id}/origin` | A origem do conceito. Por problema ligado, o enunciado, as justificativas traduzidas, o trecho e as soluções amostradas | — |
| `POST /knowledge-components/approve` | Aprova os KCs do assignment, recusada com 409 enquanto houver problema sem KC | `POST /knowledge-components/approve-qmatrix` |
| `POST /training-jobs` | Dispara o treino | `POST /training` |
| `GET /training-jobs/{job_id}` | Progresso do treino | `GET /training/{job_id}` |
| `GET /training-jobs/{job_id}/loss-history` | A curva de loss por época | `GET /training/{job_id}/metrics` |
| `GET /mastery-dashboard/{assignment_id}/mastery` | O bloco "o que o modelo prevê": conceitos e problemas por domínio previsto, com a distribuição dos alunos e o modelo | `GET /dashboard/mastery/{id}`, `/recommendations` |
| `GET /mastery-dashboard/{assignment_id}/students` | Uma linha leve por aluno, todos de uma vez; a ordenação é do front | — |
| `GET /mastery-dashboard/{assignment_id}/students/{student_id}` | O detalhe de um aluno para o diálogo | — |
| `GET /mastery-dashboard/{assignment_id}/submission-statistics` | O bloco "o que aconteceu": problemas e conceitos por taxa de acerto, desde a importação | `/pre-training-statistics`, `GET /dashboard/eda/{id}` |

Os campos do JSON seguem os nomes deste glossário, em `snake_case`.
