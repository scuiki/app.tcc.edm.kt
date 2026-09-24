# Decisões

As escolhas não óbvias do código, com o porquê completo. No código fica só uma linha curta. Aqui
fica o raciocínio, para ninguém "consertar" o que foi feito de propósito.

## Reprodutibilidade científica

**O treino usa só eventos `Run.Program`.** É o que Shi et al. (2022) e o TCC 1 fizeram. No A439
real, os `Compile.Error` são 57,6% das linhas, e treinar com eles derrubou o first-attempt AUC para
0,6959, fora da banda. O recorte é montado num lugar só (`load_training_dataset`), porque antes
treino e inferência liam o dado cada um por si e os dois esqueceram o filtro. O `Compile.Error`
continua no dado limpo, porque as estatísticas pré-treino precisam dele.

**A banda de ±3pp do teste de regressão.** Ela absorve a variação de seed do TCC 1 (desvio de cerca
de 1,34pp) e a diferença entre os hiperparâmetros congelados (protocolo de Shi et al.,
`hidden_dim=128`) e o melhor da grade do TCC 1, que gerou a referência (`hidden_dim=200`).

**O dado do teste de regressão.** É o CSEDM real, variante CodeWorkout, Spring 2019, A439, só com
`Run.Program`, que é o filtro do TCC 1. O rótulo é `Score == 1.0`. A partição treino/teste usa
`random_state=1`, e não a seed 42 do treino, para reproduzir a partição de referência.

**`is_first_attempt` é calculado antes do truncamento.** A flag sai da sequência completa do aluno
e só depois a sequência é cortada em `max_len`. O port literal do TCC 1 recalculava dentro da
janela truncada, marcava repetições como primeira tentativa e inflava o first-attempt AUC em
13,6pp.

**A atenção do Code-DKT faz softmax em `dim=2`.** Sobre os R paths, como o paper descreve. O
repositório oficial usa `dim=1`. A divergência é consciente.

**De onde vêm os hiperparâmetros.** `CODE_DKT_HYPERPARAMETERS` vem do notebook
`06_code_dkt.ipynb` do TCC 1 (o `DEFAULT_CONFIG` da célula 3 e o `BEST_CONFIG` da grade, na célula
24). Se o AUC do A439 sair da banda, é o primeiro lugar a olhar.

**A extração de AST paths depende do `PYTHONHASHSEED`.** O javalang devolve os modificadores Java
num `set`, e a ordem de um `set` de texto muda com a semente de hash do processo. Snapshots com
dois ou mais modificadores geram paths diferentes em processos diferentes. Isso explica o A439
alternar entre 0,7595 e 0,7608. O código vem do TCC 1 e a correção muda a numérica, então segue
em aberto.

**O cache de AST paths é compartilhado entre treino e inferência.** Ele guarda todos os snapshots,
inclusive os de teste, e isso é seguro porque o vocabulário só com o treino é montado depois. Ele
também garante que a inferência use os mesmos paths que o treino usou, o que re-extrair num
processo novo não garantiria (ver o item anterior).

**Na inferência, o vocabulário é o da versão treinada.** Ele é sempre recarregado do disco, nunca
reconstruído, porque reconstruir incluiria snapshots da partição de teste.

## Geração de KCs

**Os problemas são ordenados como texto.** "10" vem antes de "2", como no TCC 1. Essa ordem define
a ordem dos nomes de KC que entram no SBERT e no clustering, e portanto os grupos. Ordenar como
número mudaria os KCs.

**Poucos nomes de KC pulam o clustering.** Com menos nomes únicos que o menor número de grupos
candidato, o silhouette não se aplica, e cada nome vira o próprio grupo, sem SBERT e sem a chamada
de nomeação. É o caminho real das turmas pequenas.

**O LLM recebe o código Java cru.** Em Duan et al. (2025), Tabela 4, mandar a AST no lugar do
código piora o AUC de 0,812 para 0,784.

**Os prompts são protocolo congelado.** Eles fazem parte da chave do cache pago, e mudar uma vírgula
invalida o cache.

**A chave do cache do LLM.** Ela inclui o modelo, a versão do prompt, o prompt de sistema e o
schema, e não só o conteúdo, porque editar o sistema ou o schema devolveria em silêncio uma
resposta antiga. As partes são separadas por um byte NUL, para `("a", "b")` e `("ab", "")` não
colidirem. É identidade, não segredo.

**O LLM é chamado pela CLI `claude`.** A autenticação é o OAuth da assinatura, que só a CLI resolve.
O modelo é sempre passado por quem chama (o pin científico). A CLI roda fora do repositório
(`EDMKT_KC_CWD`), para o CLAUDE.md do projeto não entrar no contexto e no custo de cada chamada.

**Retry só para erro transitório.** Rede, 429, 5xx e timeout são refeitos com espera. Conteúdo vazio
ou inválido sobe na hora, porque refazer não muda um conteúdo já gerado e gastaria cota.

**A Q-matrix não inventa vínculos.** `build_qmatrix` bate célula a célula com o `qmatrix_A439.csv`
do TCC 1. Um problema sem KC fica com a linha zerada, e quem recusa isso é a validação da Q-matrix.

**A geração termina numa transação só.** O `mark_done()` do job roda junto com a mudança do
assignment para `kc_draft`, e uma falha desfaz os dois.

## Importação

**Só uma coisa bloqueia o treino.** É faltar uma das duas classes (acerto e erro) nos
first-attempts, porque aí o AUC é indefinido. Poucos problemas ou poucos alunos só geram avisos.
Os limiares de 50 e 20 alunos são heurísticas de cautela, marcadas `[ASSUMED]`, e a fonte delas
segue em aberto.

**O `Score` é convertido para número na leitura.** No ProgSnap2 real ele chega como `"1.0"`, vazio
ou `"N/A"`. Sem a conversão, `Score == 1.0` é falso em toda linha, e a turma inteira vira
`statistics_only` sem erro nenhum.

**Uma turma não é importada duas vezes.** A comparação é pelo slug, porque duas turmas com o mesmo
slug dividiriam o mesmo diretório em `data/`, com o cache de paths, as respostas do LLM e os
modelos de uma misturados aos da outra.

**O zip do professor não é confiável.** O nome de cada arquivo é confinado ao diretório de destino
antes de escrever, e a mensagem de erro não repete o caminho, que pode carregar conteúdo do aluno.
O teto contra zip-bomb conta os bytes realmente descomprimidos, porque o tamanho declarado no zip
é controlado por quem o mandou.

**O dado limpo volta do banco com os mesmos tipos.** O treino ordena por `submitted_at` e o `ml/`
compara ids, então um id que voltasse como texto ou um horário sem fuso mudaria a numérica sem
erro. Por isso o teste do repositório compara com `assert_frame_equal` em dtype estrito.

## Problemas

**A chave de `problem` é (`assignment_id`, `problem_id`).** O `ProblemID` do dataset só é único
dentro do assignment, e sem um id próprio do banco a `submission` e a `qmatrix` continuaram com o
`problem_id` que já tinham, sem renumerar nada.

**Quem junta problema e KC é `knowledge_components`.** A chave estrangeira vai da `qmatrix` para
`problem`, então o problema não sabe quais KCs apontam para ele, e a entidade `Problem` não carrega
KCs. A rota `/assignments/{assignment_id}/qmatrix` fica na `presentation/` de `problems`, mas a
lógica dela é um use case de `knowledge_components`. Fazer `problems` buscar os KCs criaria um
ciclo entre as duas funcionalidades.

**Um KC novo só liga problemas do próprio assignment.** Antes da FK, um `problem_id` qualquer era
aceito em silêncio. Com ela, viraria um erro do banco (500). A regra recusa o pedido antes, com a
lista dos problemas que não existem.

**A descrição de cada problema vem do LLM.** O CSEDM não traz enunciado, e na geração de KCs o LLM
deduz uma descrição a partir das soluções corretas. Ela é gravada junto com os KCs. Os problemas do
A439 estão sem descrição, porque os KCs dele foram gerados antes da tabela existir, e o cache do LLM
não guarda o `problem_id` de cada resposta. Só uma nova geração, que gasta cota, preenche.

## Dashboard

**A matriz de mastery é calculada uma vez por versão.** A versão publicada é resolvida uma vez por
chamada, para não misturar versões se um treino publicar no meio. A inferência usa o mesmo recorte
do treino. A gravação é numa transação, porque a checagem de "já calculado" só vê se existe alguma
linha, e uma matriz parcial seria servida para sempre.

**As estatísticas pré-treino leem o dado inteiro.** Ao contrário do treino, elas incluem os
`Compile.Error`, porque a taxa de erro de compilação depende deles.

**A taxa de erro de compilação é CE / Run.** E não CE / (CE + Run), que mistura os dois tipos de
evento no denominador e varia com o ritmo de tentativas de cada aluno.

## Trava de job e infraestrutura

**A trava só é liberada quando o dono morreu.** O critério é o PID não existir mais, nunca o tempo
nem "o web reiniciou". Com `--reload`, o web reinicia e o treino sobrevive, e liberar a trava ali
deixaria um segundo treino entrar na mesma GPU de 6 GB.

**Quem pega a trava é o subprocess.** É o primeiro ato do worker, para o PID dono ser o de quem pode
morrer no meio. O pré-check no web é barato e não autoritativo, porque dois pedidos em paralelo
passam por ele e o segundo perde no subprocess.

**`release()` confere o dono.** O `UPDATE` tem `WHERE holder_pid = ?`, para um release tardio de
quem já perdeu a trava não soltar a de outro job.

**`AnotherJobRunning` não é regra de negócio.** É corrida, não defeito do pedido. Tratá-la como regra
sugeriria que a exclusão mora no web e convidaria a apagar o acquire do subprocess.

**`NotFound` é separado das regras.** Ele vira 404 e as regras viram 409, e ele não acumula com as
regras, porque sem alvo não há sobre o que aplicá-las. As regras rodam todas e acumulam as recusas,
para o professor ver todos os problemas de uma vez.

**Um assignment inexistente recebe 409 nas regras de status.** O mesmo 409 de "status errado", que
é o contrato herdado do fluxo de treino e de KCs. Separar em 404 seria uma mudança de contrato.

**`settings.DATA_ROOT` nunca é importado pelo nome.** O import congela o valor, e o override do
subprocess e o monkeypatch dos testes deixariam de valer. Antes havia seis cópias, e um teste que
esquecesse uma escrevia no `data/` real.

**`connect()` usa `isolation_level=None`.** O controle de transação padrão do `sqlite3` comita
sozinho antes de DDL e quebraria a migration que aplica o DDL e o `user_version` juntos.

**O `vocab.pkl` é lido com `pickle` sem restrição.** Por isso o diretório da versão, que vem do
banco, é confinado ao `models/` da turma antes de abrir o arquivo. Um diretório adulterado viraria
execução de código.

**`CodeSnapshotId` é validado por allowlist.** É o único id do dataset do professor que vira nome de
arquivo, e aceita só letras, números e `._-`.

**`ClassroomSlug` é o único nome de turma que vira caminho.** O nome cru pode ter `/` ou `..`.

**`ProgSnapAssignmentId` é um tipo próprio.** O assignment tem dois ids inteiros, o do banco e o do
dataset, e eles já foram trocados um pelo outro.
