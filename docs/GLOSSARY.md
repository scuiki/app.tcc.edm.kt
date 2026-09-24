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
| `ClassroomSlug` | A forma segura do nome da turma que vira nome de diretório em `data/` | `TurmaSlug` |
| `Assignment` | Uma lista de exercícios (ex.: A439). Unidade de treino: um modelo por assignment | — |
| `progsnap_assignment_id` | O ID do assignment **no dataset** (439). Distinto de `Assignment.id`, o ID do banco | derivado do nome por regex |
| `Problem` / `problem_id` | Um exercício dentro do assignment, com a `description` que o LLM deduz das soluções na geração de KCs. A chave é (`assignment_id`, `problem_id`), porque o `ProblemID` do dataset só é único dentro do assignment | `ProblemID` |
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
| `TrainingEpochMetric` | A loss de uma época de um treino (a curva de loss é a lista delas) | `training_metric` |
| `KnowledgeComponentGenerationJob` | Uma geração de KCs em andamento ou concluída | `KCJob` |
| `StudentMastery` | A probabilidade de domínio de um aluno em um KC | `MasteryPrediction` |

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
| `names_including_removed()` | Os nomes dos KCs de um assignment, removidos inclusive, para o dashboard de um modelo treinado antes da remoção |

## Estados do assignment

`AssignmentStatus` descreve até onde o assignment chegou. Cada transição tem um único dono.

| Valor | Significado | Quem leva até aqui |
|---|---|---|
| `statistics_only` | Os first-attempts têm uma classe só, então o AUC é indefinido e não dá para treinar. Só as estatísticas pré-treino ficam disponíveis | importação (antes `eda_only`) |
| `ready_for_kc_generation` | Tem as duas classes; pode gerar KCs | importação (antes `trainable`) |
| `kc_draft` | KCs gerados pelo LLM, aguardando o professor | geração de KCs; ou editar KCs já aprovados |
| `kc_approved` | O professor aprovou os KCs; pode treinar | aprovação |
| `trained` | Existe um modelo publicado | treino |

Os jobs (`TrainingJob`, `KnowledgeComponentGenerationJob`) têm os estados `pending`,
`running`, `done` e `failed`.

## Dashboard

| Nome no código | O que é | Nome antigo |
|---|---|---|
| `MasteryLevel` (`low` / `medium` / `high`) | A faixa de domínio: abaixo de 0,40 / de 0,40 a 0,70 / acima de 0,70 | band, `classify_band` |
| `classify_mastery_level()` | Em que `MasteryLevel` cai um valor de mastery (`services/mastery_classification.py`) | `classify_band` |
| `StudentMasteryMatrix` | A matriz `{(student_id, kc_id): mastery}` | — |
| `find_critical_knowledge_components()` | KCs ordenados pela mastery média da turma, do mais fraco ao mais forte | `critical_kcs` |
| `find_students_at_risk()` | Alunos com 3 ou mais KCs em nível `low` | `at_risk_students` |
| `ReinforcementRecommendation` | O que reforçar em aula, com prioridade e texto em pt-BR. Sem LLM | — |
| `recommend_reinforcement()` | Monta as `ReinforcementRecommendation` a partir dos KCs críticos (`services/reinforcement_recommender.py`) | — |
| `TrainedModelInfo` | O que acompanha todo número derivado do modelo: o first-attempt AUC e a data do treino, para o professor saber o quanto confiar. Sem modelo publicado, vem vazio | `uncertainty_frame` |
| `PreTrainingStatistics` | Estatísticas das submissões disponíveis antes de qualquer treino: taxa de acerto, curva de aprendizagem, taxa de erro de compilação | EDA, `eda.py` |
| `compute_pre_training_statistics()` | Calcula as `PreTrainingStatistics` do dado limpo (`services/pre_training_statistics_calculation.py`) | `PreTrainingStatistics.of()` |
| `first_attempt_auc` | A métrica primária: AUC só sobre as primeiras tentativas | `first_auc` |

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
| `AstPathCache` | Os paths já extraídos, salvos em disco por snapshot | `features_cache` |
| `java_parse_rate` | A fração dos snapshots que o javalang conseguiu parsear | `parse_rate` |
| `ModelProvenance` | O commit do código e o hash do dado que geraram um modelo | `provenance` |
| `CODE_DKT_HYPERPARAMETERS` | Os hiperparâmetros de Shi et al. 2022, imutáveis | `FROZEN_CONFIG` |
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
| `GET /assignments` | Lista os assignments | igual |
| `GET /assignments/{assignment_id}/problems` | Os problemas do assignment, com a descrição | — |
| `GET /assignments/{assignment_id}/problems/knowledge-components` | Cada problema com a descrição e os KCs que exige (a lógica é de `knowledge_components`) | — |
| `GET /knowledge-components?assignment_id=…` | Os KCs do assignment, cada um com os `problem_ids` a que se liga | — |
| `POST /knowledge-components/{kc_id}/problems/{problem_id}` | Liga um KC que já existe a mais um problema | — |
| `DELETE /knowledge-components/{kc_id}/problems/{problem_id}` | Tira o KC de um problema só; se ele perder o último, sai junto | — |
| `POST /classroom-imports` | Recebe o `.zip` e devolve os arquivos detectados | `POST /ingest` |
| `POST /classroom-imports/process` | Importa a variante escolhida | `POST /ingest/process` |
| `POST /knowledge-components/generation-jobs` | Dispara a geração de KCs | `POST /kc/generate` |
| `GET /knowledge-components/generation-jobs/{job_id}` | Progresso da geração | `GET /kc/jobs/{job_id}` |
| `POST /knowledge-components` | O professor adiciona um KC | `POST /kc` |
| `PATCH /knowledge-components/{kc_id}` | Renomeia um KC | `PATCH /kc/{kc_id}` |
| `DELETE /knowledge-components/{kc_id}` | Remove um KC | `DELETE /kc/{kc_id}` |
| `POST /knowledge-components/merge` | Funde dois KCs | `POST /kc/merge` |
| `POST /knowledge-components/approve` | Aprova os KCs do assignment | `POST /knowledge-components/approve-qmatrix` |
| `POST /training-jobs` | Dispara o treino | `POST /training` |
| `GET /training-jobs/{job_id}` | Progresso do treino | `GET /training/{job_id}` |
| `GET /training-jobs/{job_id}/loss-history` | A curva de loss por época | `GET /training/{job_id}/metrics` |
| `GET /mastery-dashboard/{assignment_id}/mastery` | Matriz aluno × KC, KCs críticos, alunos em risco | `GET /dashboard/mastery/{id}` |
| `GET /mastery-dashboard/{assignment_id}/recommendations` | Recomendações de reforço | `GET /dashboard/recommendations/{id}` |
| `GET /mastery-dashboard/{assignment_id}/pre-training-statistics` | Estatísticas pré-treino | `GET /dashboard/eda/{id}` |

Os campos do JSON seguem os nomes deste glossário, em `snake_case`.
