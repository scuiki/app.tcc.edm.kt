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
| `Problem` / `problem_id` | Um "problema" na UI, um item dentro do assignment, com a `description` que o LLM deduz das soluções na geração de KCs. A chave é (`assignment_id`, `problem_id`), porque o `ProblemID` do dataset só é único dentro do assignment | `ProblemID` |
| `Student` / `student_id` | O aluno | `SubjectID` |
| `CodeSnapshot` / `code_snapshot_id` | O código Java que o aluno enviou numa tentativa | `CodeStateID` |
| `Submission` | Uma tentativa: aluno + problema + snapshot + nota | — |
| `is_correct` | A tentativa acertou (`score == 1.0`). É o rótulo que o modelo aprende | `correct` |
| `SubmissionEvent` | Se o código rodou (`Run.Program`) ou nem compilou (`Compile.Error`). Os **valores** seguem os do ProgSnap2 | `EventType` |
| `KnowledgeComponent` | Um conceito de programação que um problema exige (ex.: "laço com acumulador") | `KC` |
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
| `I<Entidade>Repository` (`IAssignmentRepository`, `IClassroomRepository`, `IProblemRepository`, `ISubmissionRepository`, `IKnowledgeComponentRepository`, `IKnowledgeComponentGenerationJobRepository`, `IProblemKnowledgeComponentRepository`, `ITrainingJobRepository`, `ITrainedModelRepository`, `ITrainingEpochMetricRepository`, `IStudentMasteryRepository`) | `Sqlite<Entidade>Repository` | Ler e gravar uma entidade | sem o `I` |
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
| `kc_draft` | KCs gerados pelo LLM, aguardando o professor | geração de KCs; ou editar KCs já aprovados |
| `kc_approved` | O professor aprovou os KCs; pode treinar | aprovação |
| `trained` | Existe um modelo publicado. Sem re-treino, os KCs ficam como estão; qualquer edição é recusada por `refuse_edit_after_training()` (`services/knowledge_component_edit.py`) | treino |

Os jobs (`TrainingJob`, `KnowledgeComponentGenerationJob`) têm os estados `pending`,
`running`, `done` e `failed`.

O `KnowledgeComponentGenerationJob` informa também o progresso dentro do estágio atual, em
`progress_done` e `progress_total`: quantos itens já terminaram, de quantos (problemas no `generate`,
grupos na nomeação do `cluster`). Os dois ficam vazios quando o estágio não tem itens para contar.

## Dashboard

A tela "Análise" de cada exercício entrega o dado, não a interpretação. Duas famílias, nunca na
mesma régua: "o que aconteceu" (contagens das execuções, desde a importação) e "o que o modelo
prevê" (só com modelo publicado). Sem níveis, faixas, recomendações ou cortes.

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `StudentMasteryMatrix` | A matriz `{(student_id, problem_id): mastery}`, o dado nativo do modelo | matriz aluno × KC |
| domínio (`mastery`) | A chance prevista de o aluno acertar um problema se tentasse agora, lida do último passo do Code-DKT. Não é a fração do conceito aprendida. Na tela, sempre com o marcador de cérebro (`EstimatedMark`) e a dica com essa frase | — |
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
| dado estimado (`GeneratedByML`) | O marcador de cérebro antes do rótulo de toda coluna que vem do Code-DKT | `EstimatedMark`, badge "previsto" |
| gerado pelo modelo de linguagem (`GeneratedByLLM`) | O marcador de estrelas no que o LLM escreveu, o nome do conceito e a descrição do problema. Some do nome quando o professor o renomeia | — |
| recorrência (`recurrence`) | Em quantos problemas do exercício um conceito aparece. Com um só, o valor do conceito é o desse problema, evidência fraca | cobertura |
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
| `SampledSolution` | Uma das até cinco soluções corretas que o KCGen-KT sorteou para um problema, a primeira de um aluno, uma por faixa de tentativas até acertar. Gravada na extração, pelo `code_snapshot_id` | — |
| origem do conceito | O diálogo com as soluções sorteadas de cada problema em que o conceito aparece | — |

## Importação

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `n_students_eligible` | Quantos alunos de um exercício têm ao menos uma execução `Run.Program`, os que entram na partição | — |
| `PackageRequirement` | Um requisito do pacote ProgSnap2 (tabela de eventos, código dos alunos, formato ProgSnap2 v6, até 512 MB), conferido depois do envio, atendido ou não | "O que veio no pacote" |

## Pipeline de dados

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `classroom_import` | Receber o `.zip` ProgSnap2, validar, limpar e persistir | `ingestion` |
| `ClassroomImportReport` / `ImportCheck` | O relatório da importação e cada item dele (fatal, aviso ou de treinabilidade) | `IngestReport` / `ReportItem` |
| `check_assignment_trainability()` | Decide, por assignment, entre `ready_for_kc_generation` e `statistics_only` | `viability` |
| tabela `submission` | O dado limpo de onde tudo lê (`ISubmissionRepository.list_by_assignment()`), com o código Java | Parquet por assignment (`cleaned_submissions.parquet`) |
| `TrainingDataset` | O recorte que treino e inferência consomem: só eventos `Run.Program` | `ModelingFrame` |
| `load_training_dataset()` | Monta o `TrainingDataset` de um assignment (`services/training_dataset_loading.py`) | `load_modeling_frame` |
| `TrainingOutcome` | O que um treino devolve: o modelo, o vocabulário, os hiperparâmetros, o first-attempt AUC e o `java_parse_rate` | — |
| `DetectedUpload` | O que o upload encontrou no `.zip`: o diretório cru e as tabelas | — |
| `AstPath` | Um caminho na árvore sintática do Java; é a feature de entrada do Code-DKT (termo do artigo) | paths |
| `AstPathCache` | Todos os paths de cada solução, já extraídos e salvos em disco por snapshot, num diretório com a `AST_PATH_CACHE_VERSION`. O sorteio dos R acontece depois, na montagem da entrada | `features_cache` |
| `AST_PATH_CACHE_VERSION` | A versão do método de extração no diretório do `AstPathCache`. Um cache de outra versão é ignorado | — |
| `PADDING_INDEX` | O índice 0 dos vocabulários de nós e de paths, que preenche as posições vazias, as de uma solução com menos de R paths e as antes da primeira execução de quem tem menos de 50 | — |
| `UNKNOWN_INDEX` | O índice 1 dos vocabulários, de um nó ou path que não apareceu no treino. Os tokens reais começam no 2 | índice 0 do OOV |
| `sample_ast_paths()` | O sorteio dos R paths de uma solução com a `path_sampling_seed`, só quando ela tem mais de R paths, usado no treino, na avaliação e na inferência | — |
| `path_sampling_seed` | A seed do sorteio dos R paths de cada solução, 42, separada da `seed` do treino para os paths não mudarem entre as execuções | `seed` |
| `code_vector_layer` | A camada linear sem viés que leva a média ponderada dos paths ao vetor de código z, o W_0 de Shi et al. (2022) | — |
| `INFERENCE_CHUNK_SIZE` | Quantos alunos entram de cada vez num forward da inferência e da avaliação, para a memória não estourar | — |
| `batch_chunk_size` | Quantos alunos de um lote entram de cada vez no forward e no backward do treino, com o gradiente somado até completar o lote, para a memória da GPU não estourar | — |
| `EVALUATION_SEEDS` | As seeds das dez execuções da avaliação, de 42 a 51 | — |
| `evaluate_over_seeds()` | Treina e avalia um exercício uma vez por seed de `EVALUATION_SEEDS` (`ml/evaluation/seed_evaluation.py`) | multirun do TCC 1 |
| `SeedEvaluation` | O resultado de `evaluate_over_seeds()`, com o AUC de cada seed, a média e o desvio | — |
| `TRAINED_MODEL_FORMAT_VERSION` | A versão do formato do artefato de um `TrainedModel`, gravada como `format_version` no `config.json` | — |
| `IncompatibleTrainedModelError` | O erro de quando um artefato não tem a `format_version` atual. Vira 409 | — |
| marcador `literature` | O teste que compara o app com as Tabelas 1 e 2 de Shi et al. (2022), `tests/test_literature_comparison.py`, fora da suíte padrão | — |
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
| 1 | `select_sample_solutions()` | Escolhe até 5 soluções corretas e diversas por problema | `diversity_sample` |
| 2 | `generate_candidate_kcs()` | Pede ao LLM os KCs que cada problema exige | `generate_kcs_for_problem` |
| 3 | `choose_kc_group_count()` + `group_similar_kcs()` | Escolhe quantos grupos (silhouette) e agrupa os nomes de KC parecidos (SBERT + clustering hierárquico) | `select_best_n_clusters`, `_cluster_with_n` |
| 4 | `name_kc_group()` | Pede ao LLM um nome para cada grupo | `label_cluster` |
| 5 | `build_qmatrix()` | Monta a Q-matrix problema × KC | `build_qmatrix` |
| — | `LLMResponseCache` | As respostas do LLM guardadas por hash, para não pagar duas vezes | `kc_cache` |
| — | `LLMClient` | A interface do LLM que o `ml/` declara e a `api/` implementa | `ports.LLMClient` |

## Rotas HTTP

| Rota | O que faz | Rota antiga |
|---|---|---|
| `GET /assignments` | Lista os assignments ativos; com `?classroom_id=…`, só os da turma | igual |
| `GET /assignments/{assignment_id}/problems` | Os problemas do assignment, com a descrição | — |
| `GET /assignments/{assignment_id}/problems/knowledge-components` | Cada problema com a descrição e os KCs que exige (a lógica é de `knowledge_components`) | — |
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
| `POST /knowledge-components` | O professor adiciona um KC | `POST /kc` |
| `PUT /knowledge-components/{kc_id}` | Renomeia um KC | `PATCH /knowledge-components/{kc_id}` |
| `DELETE /knowledge-components/{kc_id}` | Remove um KC | `DELETE /kc/{kc_id}` |
| `POST /knowledge-components/merge` | Funde dois KCs | `POST /kc/merge` |
| `POST /knowledge-components/approve` | Aprova os KCs do assignment | `POST /knowledge-components/approve-qmatrix` |
| `POST /training-jobs` | Dispara o treino | `POST /training` |
| `GET /training-jobs/{job_id}` | Progresso do treino | `GET /training/{job_id}` |
| `GET /training-jobs/{job_id}/loss-history` | A curva de loss por época | `GET /training/{job_id}/metrics` |
| `GET /mastery-dashboard/{assignment_id}/mastery` | O bloco "o que o modelo prevê": conceitos e problemas por domínio previsto, com a distribuição dos alunos e o modelo | `GET /dashboard/mastery/{id}`, `/recommendations` |
| `GET /mastery-dashboard/{assignment_id}/students` | Uma linha leve por aluno, todos de uma vez; a ordenação é do front | — |
| `GET /mastery-dashboard/{assignment_id}/students/{student_id}` | O detalhe de um aluno para o diálogo | — |
| `GET /mastery-dashboard/{assignment_id}/submission-statistics` | O bloco "o que aconteceu": problemas e conceitos por taxa de acerto, desde a importação | `/pre-training-statistics`, `GET /dashboard/eda/{id}` |

Os campos do JSON seguem os nomes deste glossário, em `snake_case`.
