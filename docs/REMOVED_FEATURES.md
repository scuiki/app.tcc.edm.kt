# Funcionalidades retiradas

O que saiu da interface e como voltar. Cada seção diz o que existia, o commit que retirou, o último
commit em que a funcionalidade ainda estava inteira, o que continua no backend e os passos para
trazer de volta. Uma volta entra com uma decisão nova no `DECISIONS.md`, no lugar da que retirou.

## Curva de perda no diálogo de treino

Retirada em 03/11/2026 no commit `a2b0f2d`. O último estado com a curva é o `0a933eb`.

O diálogo de treino mostrava, enquanto o job rodava e de novo ao terminar, um gráfico de linha com a
perda média por aluno em cada época, com o último valor marcado. Ao lado do gráfico havia uma tabela
escondida com as mesmas épocas, lida pelo leitor de tela e pelos testes. O professor não decidia nada
pela perda, e a lista de estágios com a época atual já mostrava que o treino andava, então a curva
saiu e levou junto o Chart.js, a única biblioteca de gráficos do front.

### O que existia no front

| Arquivo no `0a933eb` | O que tinha |
|---|---|
| `src/web/src/features/mastery_dashboard/components/LossChart.tsx` | O componente, um `Line` do `react-chartjs-2` numa `figure` chamada "Perda de treino por época", com a cor lida do token `--color-model` e a tabela escondida |
| `src/web/src/features/mastery_dashboard/components/LossChart.css` | A altura do canvas |
| `src/web/src/features/model_training/api/training.ts` | O tipo `TrainingLossHistory`, a chave `trainingKeys.lossHistory` e o `useLossHistory`, que consultava o histórico a cada 2 s enquanto o job rodava |
| `src/web/src/features/mastery_dashboard/useTraining.ts` | O `epochs` no retorno do hook e a invalidação do histórico no fim do treino, que buscava as épocas finais, gravadas depois da última consulta |
| `src/web/src/features/mastery_dashboard/components/TrainingDialog.tsx` | O `LossChart` nas visões "Treino em andamento" e "Modelo treinado" |
| `src/web/src/test/setup.ts` | O mock do `react-chartjs-2`, porque o jsdom não tem canvas |
| `src/web/src/features/mastery_dashboard/pages/MasteryDashboardPage.test.tsx` | As épocas falsas (`EPOCHS`), a rota falsa do `loss-history` e a conferência da linha "Época 2" com 0,61 |
| `src/web/package.json` | `chart.js` 4.5.1 e `react-chartjs-2` 5.3.1 (o lock trazia também o `@kurkle/color`) |

### O que continua no backend

Nada mudou no backend. O treino segue gravando a perda de cada época.

| Peça | Onde |
|---|---|
| A gravação por época | `src/api/model_training/application/use_cases/run_training_use_case.py` |
| A entidade e a tabela | `TrainingEpochMetric`, tabela `training_metric` |
| A leitura | `get_training_loss_history_use_case.py` |
| O endpoint | `GET /training-jobs/{job_id}/loss-history`, em `training_controller.py` |
| O tipo no front | `TrainingLossHistoryDTO`, ainda no `src/web/src/http/schema.d.ts` gerado |

### Os docs que mudaram

O texto antigo está no `0a933eb`. Mudaram, no `DECISIONS.md`, a decisão "O Chart.js desenha só a
curva de perda" e o trecho da curva na decisão do diálogo de treino, e, no `DESIGN.md`, as regras
da curva e o uso do `--color-model`. Também mudaram o parágrafo de estilo do `ARCHITECTURE.md`, a
tabela da stack do `CLAUDE.md`, as linhas do `TrainingEpochMetric` e do endpoint no `GLOSSARY.md` e
o bloco F4 do `IMPLEMENTATION_PLAN.md`.

### Como voltar

1. Registrar a decisão nova no `DECISIONS.md`, no lugar de "O diálogo de treino não mostra a curva
   de perda".
2. Devolver o código. Se os arquivos em volta pouco mudaram, `git revert a2b0f2d` desfaz tudo de
   uma vez. Senão, cada arquivo sai de `git show 0a933eb:<caminho>`.
3. Devolver as dependências dentro do container, nunca no host, com
   `docker compose exec web npm install --save-exact chart.js@4.5.1 react-chartjs-2@5.3.1`.
4. Rodar o Vitest, o `tsc -b` e o eslint no container.

## A seção de avisos sempre visível e o aviso da compilação repetida

Retirados em 03/11/2026 no commit `af8508b`. O último estado anterior é o `0a933eb`.

No fim da importação, o cartão "O que foi importado" sempre tinha a seção "Avisos do processamento".
Sem aviso, ela dizia "Nenhum aviso. O sistema não precisou ajustar nada." Na base CSEDM ela listava
"Compilações repetidas descartadas", com a mensagem do backend sobre os 69.627 eventos `Compile`
descartados. Esse descarte é o formato esperado do ProgSnap2, não um ajuste no dado do professor,
então a tela passou a ignorar o `dedup_compile`, e a seção só aparece quando sobra algum aviso.

### O que existia no front

| Arquivo no `0a933eb` | O que tinha |
|---|---|
| `src/web/src/features/classroom_import/importReport.ts` | O título `dedup_compile: 'Compilações repetidas descartadas'` no `CHECK_TITLES`, e o `warningsOf` sem o filtro do `dedup_compile` |
| `src/web/src/features/classroom_import/components/ImportResult.tsx` | O traço, o título e a frase final da seção sempre visíveis, com o texto de "Nenhum aviso" quando a lista vinha vazia |
| `src/web/src/features/classroom_import/importReport.test.ts` e `pages/ClassroomImportPage.test.tsx` | Os testes que esperavam o aviso da compilação repetida na tela |

### O que continua no backend

Nada mudou no backend. O `src/api/classroom_import/domain/services/submission_cleaning.py` segue
mandando o `dedup_compile` com severidade `warning` e a contagem no relatório da importação.

### Como voltar

1. Registrar a decisão nova no `DECISIONS.md`, no lugar de "A compilação repetida não é aviso da
   importação".
2. Para tudo voltar como era, `git revert af8508b`.
3. Para voltar só uma das duas partes, devolver o título ao `CHECK_TITLES` e tirar o filtro do
   `warningsOf` para o aviso aparecer, ou tirar a condição `warnings.length > 0` do `ImportResult`
   para a seção aparecer sempre, com o texto de "Nenhum aviso" de volta.
