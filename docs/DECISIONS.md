# Decisões

As escolhas não óbvias do código, com o porquê completo. No código fica só uma linha curta. Aqui
fica o raciocínio, para ninguém "consertar" o que foi feito de propósito.

## Reprodutibilidade científica

O método do Code-DKT, o que o app segue do paper e do repositório oficial e onde diverge, está no
`DEVELOPMENT.md`. Aqui ficam as escolhas de engenharia em volta dele, com o ponteiro para a decisão
do `DEVELOPMENT.md` que trata do método (o número da linha e o assunto), quando há uma.

**O treino usa só eventos `Run.Program`.** É o que Shi et al. (2022) e o TCC 1 fizeram. No A439
real, os `Compile.Error` são 57,6% das linhas, e treinar com eles derrubou o first-attempt AUC para
0,6959, numa medida anterior às mudanças de fidelidade ao paper (etapas 1 a 6 do
`CODE_DKT_PLAN.md`). O recorte é montado num lugar só (`load_training_dataset`), porque antes treino
e inferência liam o dado cada um por si e os dois esqueceram o filtro. O `Compile.Error` continua no
dado limpo, porque as estatísticas das execuções precisam dele.

**A tolerância do teste de regressão é de ±0,1 ponto (±0,001 de AUC).** O teste roda as dez seeds no
A439 e confere que a média do first-attempt AUC fica a 0,1 ponto da média de referência, 0,7278, o
valor que o app mediu em 02/10/2026. As dez seeds se repetem bit a bit na mesma máquina, então
qualquer mudança na média quer dizer que o código, as dependências ou o ambiente mudaram. O teste
detecta essa mudança, e não serve de valor de referência científico contra o TCC 1 nem contra o
paper. Falha sem GPU, porque a média de referência foi medida nela. A decisão está na linha 19 do
`DEVELOPMENT.md`, a regressão e a comparação com o paper.

**O dado do teste de regressão.** É o CSEDM real, variante CodeWorkout, Spring 2019, A439, só com
`Run.Program`, que é o filtro do TCC 1. O rótulo é `Score == 1.0`. A partição treino/teste é a do
repositório oficial, a mesma do treino real, com `random_state=1` e não a seed 42 do treino
(a linha 13 do `DEVELOPMENT.md`, a partição).

**`is_first_attempt` é calculado antes do truncamento.** A flag sai da sequência completa do aluno
e só depois a sequência é cortada em `max_len`. O port literal do TCC 1 recalculava dentro da
janela truncada, marcava repetições como primeira tentativa e inflava o first-attempt AUC em
13,6pp (a linha 11 do `DEVELOPMENT.md`, a primeira tentativa).

**A atenção do Code-DKT faz softmax em `dim=2`.** Sobre os R paths, como o paper descreve. O
repositório oficial usa `dim=1`. A divergência é consciente (a linha 5 do `DEVELOPMENT.md`, o eixo
do softmax).

**De onde vêm os hiperparâmetros.** Cada valor de `CODE_DKT_HYPERPARAMETERS` tem a fonte no
`DEVELOPMENT.md` (o R na linha 1, a dimensão do estado oculto (hidden size) e o tamanho do lote
(batch size) na linha 14, as seeds na linha 18), e o que o paper e o repositório não definem é
decisão do app. Se a média do A439 sair da tolerância do teste de regressão, é o primeiro lugar a
olhar.

**A extração de AST paths depende do `PYTHONHASHSEED`.** O javalang devolve os modificadores Java
num `set`, e a ordem de um `set` de texto muda com a semente de hash do processo. Snapshots com
dois ou mais modificadores geram paths diferentes em processos diferentes. Era isso que fazia o
first-attempt AUC do A439 alternar de uma execução para outra. O app mantém o código do repositório
e fixa o `PYTHONHASHSEED=0` no `Dockerfile` base, que a imagem do app herda, decisão da linha 2 do
`DEVELOPMENT.md`, a ordem dos modificadores Java. A asserção de `ast_paths_test.py` e a da fixture
da CSEDM falham, sem pular, num processo com outro valor.

**O cache de AST paths é compartilhado entre treino e inferência.** O `MlCodeDktTrainer` passa ao
`train_and_evaluate` os paths lidos do cache, e a inferência lê o mesmo cache, então os dois partem
dos mesmos paths de cada solução (antes o treino extraía por conta própria). O cache guarda todos os
paths de cada solução e todos os snapshots, inclusive os de teste, e isso é seguro porque o
vocabulário só com o treino e a amostragem aleatória dos R paths vêm depois, na montagem da entrada.
A mesma ordem dos paths entre processos vem do `PYTHONHASHSEED` fixo (item anterior), e não do
cache. A pasta leva a `AST_PATH_CACHE_VERSION` no nome, e o cache da pasta `paths` sem versão, que
guardava só a amostra, fica no disco, ignorado.

**Na inferência, o vocabulário é o da versão treinada.** Ele é sempre recarregado do disco, nunca
reconstruído, porque reconstruir incluiria snapshots da partição de teste.

**Um artefato de outro formato é recusado, e não lido.** O `config.json` de cada modelo guarda a
`format_version`, e o artefato sem a versão atual é recusado com o `IncompatibleTrainedModelError`,
uma resposta 409 com mensagem clara. As mudanças de fidelidade do Code-DKT (o W_0, o vocabulário
com o token desconhecido (UNK) no índice 1, o cache com todos os paths) tornam os modelos antigos
ilegíveis. O W_0 faria a leitura quebrar com um erro cru, e o vocabulário antigo seria lido sem erro
nenhum, com o token desconhecido caindo num token real. A recusa troca as duas falhas por uma
mensagem. A matriz de domínio já gravada de um modelo antigo continua servindo o painel, porque não
recarrega o modelo.

**A curva de perda mostra a perda média por aluno.** O treino soma, em cada lote, a perda média de
cada aluno, como o repositório do Code-DKT, e esse número cresce com o tamanho do lote e da turma.
Cada `TrainingEpochMetric` guarda a soma da época dividida pelos alunos que entraram na perda, os que
têm ao menos uma previsão válida, e a curva fica na mesma escala para qualquer turma. O treino não
muda (a agregação da perda é a da linha 16 do `DEVELOPMENT.md`).

**O treino usa acumulação de gradiente em batches de 64 alunos.** Com R=100, o bloco de atenção do
Code-DKT cria tensores de 128 × 50 × 100 × (2M + 300) floats, 819 MB cada no A439, e o autograd
guarda vários deles para o `backward`. O lote de 128 inteiro estourou a memória da RTX 4050, que tem
6 GB e também alimenta a tela do desktop. O `batch_chunk_size` aplica a acumulação de gradiente em
batches de 64 e dá um passo do Adam por lote de 128, com pico de 3.187 MiB no `nvidia-smi`. A
memória depende só das formas dos tensores, e não do conteúdo, então o pico é previsível e cresce
pouco com o número de problemas. O tamanho do batch de acumulação é fixo e fica gravado com o
modelo, porque escolhê-lo pela memória livre faria o resultado depender do que mais estivesse aberto
na máquina. Mudar só o alocador do PyTorch (`expandable_segments`) mantinha o lote inteiro com o
resultado numérico idêntico, mas o pico ficava em 5.345 de 6.141 MiB. Recalcular as ativações no
`backward` (checkpoint) quase não economiza aqui, porque a memória fica num bloco só, e reduzir o R
ou o lote mudaria o método. A decisão está na linha 14 do `DEVELOPMENT.md`, o tamanho do lote e a
acumulação de gradiente.

**A comparação com o paper roda à parte e não falha pelos números.** O teste do marcador
`literature` treina os cinco exercícios da CSEDM com as dez seeds e imprime a tabela ao lado das
Tabelas 1 e 2 de Shi et al. (2022), sem asserção contra elas. As correções do app ao repositório,
como a ordem por tempo, podem afastar o número do paper de forma legítima, e um teste que exigisse o
número do paper empurraria o código de volta para os defeitos. Ele fica fora da suíte padrão porque
leva cerca de 19 minutos na GPU, e falha só por erro de execução ou por AUC indefinido.

## Geração de KCs

**O KCGen-KT segue Duan et al. (2026).** O método, as fontes e o porquê de cada escolha estão na
seção KCGen-KT do `DEVELOPMENT.md`, que está sendo levada ao código pelo `KCGEN_KT_PLAN.md`. As
entradas abaixo guardam as decisões de engenharia em volta do método e descrevem o que o plano leva
ao código, e o código pode divergir delas até o plano terminar.

**Os problemas entram em ordem numérica.** A ordem em que os nomes de KC entram no agrupamento não
muda os grupos, salvo empates nas distâncias, mas muda a numeração deles e o texto dos pedidos de
nomeação, que faz parte da chave do cache. A ordem de texto, com "10" antes de "2", era dada como
fiel ao TCC 1, que na verdade ordena por número (a ordem de entrada dos nomes, na linha 21 do
KCGen-KT no `DEVELOPMENT.md`).

**O número de grupos sai da proporção do paper.** São 50/103 dos nomes únicos do exercício, com pelo
menos um grupo, o nível que o paper escolheu na CodeWorkout (o número de grupos e os poucos nomes,
nas linhas 19 e 20 do KCGen-KT no `DEVELOPMENT.md`). Um nome só vira um grupo sem passar pelo HAC,
que precisa de dois. O silhouette entre 10, 12 e 15 do TCC 1 sai, e com ele o caminho especial das
turmas pequenas e a falha com exatamente 10 nomes.

**O CodeBERT usa a GPU.** A extração e o treino nunca rodam juntos, porque o `OneJobAtATimeLock`
serializa os dois, então o CodeBERT não disputa a GPU com o treino. Ele a usa sempre que ela existe,
para a extração sair rápido, mesmo que os vetores variem um pouco de uma execução para outra. É a
escolha do Leo em 04/10/2026, que pôs a rapidez para o professor na frente da repetição exata dos
vetores.

**Os modelos de vetores vêm na imagem base, com a revisão fixada.** O CodeBERT e o SBERT são
baixados no build da `edmkt-core:dev`, que o app herda, e o app roda com o Hugging Face offline. Os
testes e o app usam os mesmos arquivos, e uma revisão nova publicada no Hugging Face não muda os
vetores em silêncio. O `transformers`, o `tokenizers`, o `huggingface_hub` e o `safetensors` têm
versão fixada pelo mesmo motivo, e a conversão automática do `transformers` para outro formato de
pesos fica desligada, porque ela baixaria arquivos de fora da revisão fixada.

**O LLM recebe o código Java cru.** Em Duan et al. (2026), Tabela 4, mandar a AST no lugar do
código piora o AUC de 0,812 para 0,784.

**Os prompts do Duan são copiados, e não escritos.** O de geração é o texto do `KC_gen.py` do
repositório oficial, e o de nomeação é o da Tabela 10 do paper, mudados só onde o dado obriga (os
textos dos prompts, nas linhas 12, 13 e 22 do KCGen-KT no `DEVELOPMENT.md`). Eles fazem parte da
chave do cache de respostas do LLM, e cada chamada gasta cota da assinatura, então qualquer mudança
sobe o `PROMPT_VERSION`. Os prompts dos trechos e da tradução são do app, revisados pelo Leo antes
de qualquer chamada real.

**A chave do cache do LLM.** Ela inclui o modelo, a versão do prompt, o prompt de sistema e o
schema, e não só o conteúdo, porque editar o sistema ou o schema devolveria em silêncio uma
resposta antiga. As partes são separadas por um byte NUL, para `("a", "b")` e `("ab", "")` não
colidirem. É identidade, não segredo. Uma resposta só entra no cache depois de validada, então uma
resposta fora do formato nunca é devolvida de novo.

**O LLM é chamado pela CLI `claude`.** A autenticação é o OAuth da assinatura, que só a CLI resolve.
O modelo é sempre passado por quem chama, o Claude Sonnet 5.5 (`claude-sonnet-5-5`), um modelo
forte, a adaptação mais próxima do GPT-4o do paper (o LLM, na linha 9 do KCGen-KT no
`DEVELOPMENT.md`). Ele não tem versão datada, então o job
grava o modelo e a versão do prompt de cada extração. Os prompts do Duan pedem o JSON no próprio
texto, então a chamada vai sem schema, e a resposta é lida do texto e validada pelo app. A CLI roda
fora do repositório (`EDMKT_KC_CWD`), para o CLAUDE.md do projeto não entrar no contexto e no custo
de cada chamada.

**Retry para erro transitório e para resposta inválida.** Rede, 429, 5xx e timeout são refeitos com
espera, e uma resposta vazia, que não é JSON ou que está fora do formato pedido também, até 3 vezes
ao todo. A temperatura não é fixável no modelo nem na CLI, então uma chamada nova pode vir certa.
Depois da terceira, a extração para com erro.

**As chamadas de um estágio rodam em paralelo, até 4 de cada vez.** As chamadas do `generate` e do
`evidence` (uma por problema) e as da nomeação (uma por grupo) não dependem umas das outras, e em
sequência a extração de 10 problemas levava uns 8 minutos. O paralelismo fica só no gerador da
`api/`, e a amostragem das soluções continua em sequência e na ordem anterior ao paralelismo, os
prompts são os mesmos, e os resultados são juntados por problema e por grupo, então a ordem em que
as chamadas terminam não muda nada do que o KCGen-KT vê. O limite de 4 é para não esbarrar no limite
de uso da assinatura. O cache de respostas grava o arquivo inteiro a cada resposta e por isso tem
uma trava, e o progresso do job é gravado pela thread que disparou as chamadas, então a conexão
SQLite do worker nunca é usada por duas threads ao mesmo tempo.

**A CLI roda sem ferramenta nenhuma (`--tools ""`).** Medido no container, cada chamada custa uns 5
segundos fixos para a CLI subir, e nenhuma flag reduz isso. Sem ferramentas, somem do contexto as
definições delas, cerca de 9.600 tokens de entrada por chamada (numa chamada mínima, de 10.766 para
1.112). Isso poupa a cota da assinatura, o que pesa com 4 chamadas ao mesmo tempo, e fecha de vez
qualquer I/O do LLM. `--strict-mcp-config` e `--no-session-persistence`
não mudam o tempo hoje, mas impedem que um servidor MCP do host suba a cada chamada e que sessões
se acumulem em disco. O cache não inclui as flags na chave, porque elas não mudam o prompt.

**O job informa quantos itens do estágio já terminaram.** `progress_done` e `progress_total`
mostram o "7 de 10" do diálogo, em problemas no `generate` e no `evidence` e em grupos na nomeação.
Um estágio novo começa sem progresso, para a tela nunca mostrar a contagem do anterior. Os estágios
são cinco, `generate`, `cluster`, `qmatrix`, `evidence` e `translate`, e a tela tem um texto para
cada um, porque um estágio que ela não conhece deixa o diálogo parado no primeiro até o fim.

**A Q-matrix não inventa vínculos.** `build_qmatrix`, no `ml/`, bate célula a célula com a Q-matrix
da extração de referência da CSEDM, no teste das partes sem LLM do KCGen-KT. Um problema sem KC fica
com a linha zerada, e quem recusa isso é a validação da geração. Na aplicação, cada célula 1 vira um
`ProblemKnowledgeComponent`.

**A geração termina numa transação só.** O `mark_done()` do job roda junto com a mudança do
assignment para `kc_draft` e com a gravação dos conceitos, das soluções amostradas, dos KCs
candidatos e dos trechos, e uma falha desfaz tudo.

**O conceito guarda o nome gerado e o nome mostrado.** O nome gerado, em inglês e em minúsculas, é o
resultado do método e fica como registro. O nome mostrado, em português, sai de uma tradução depois
da extração, e é o que o professor lê e renomeia. Renomear muda só o nome mostrado.

**A extração grava as soluções amostradas, os KCs candidatos e os trechos.** A solução amostrada
aponta para a execução escolhida, que já tem o aluno, o horário e o código, e para o problema, que
leva ao exercício e à turma, então nada disso é repetido. O KC candidato guarda a justificativa de
cada KC, em inglês e em português, e o conceito em que caiu. O trecho aponta para a solução
amostrada. É o que a origem do conceito mostra e o que os testes de regressão da extração usam.

**O enunciado é opcional e vem de um arquivo do pacote.** O ProgSnap2 não traz enunciado, e o da
CSEDM está numa planilha oficial à parte. O upload aceita um arquivo só, então o arquivo de
enunciados vai dentro do zip, e a importação o acha pelo cabeçalho da planilha oficial
(`AssignmentID`, `ProblemID` e `Requirement`), porque o nome dele não é padrão. Sem ele, a
importação e a extração rodam como antes, e o prompt sai sem as duas linhas do enunciado.

## Importação

**Só uma coisa bloqueia o treino.** É faltar uma das duas classes (acerto e erro) nos
first-attempts, porque aí o AUC é indefinido. Poucos problemas ou poucos alunos só geram avisos.
Os limiares de 50 e 20 alunos são heurísticas de cautela, anotadas no código como sem fonte, e
a fonte delas segue em aberto.

**O `Score` é convertido para número na leitura.** No ProgSnap2 real ele chega como `"1.0"`, vazio
ou `"N/A"`. Sem a conversão, `Score == 1.0` é falso em toda linha, e a turma inteira vira
`statistics_only` sem erro nenhum.

**Os arquivos de uma turma ficam no id dela, não no nome.** Antes o diretório vinha do slug do nome,
e isso tinha dois problemas. Renomear a turma mudava o slug, e o app deixava de achar o modelo
publicado. E um segundo envio para a mesma turma misturava os arquivos brutos e reaproveitava o
cache de AST paths de outro dataset, porque a chave era só o `CodeStateID`. Agora o diretório é
`data/<classroom_id>/`, cada envio tem a própria pasta em `raw/`, e o cache de AST paths e o do LLM
ficam por assignment.

**Uma turma recebe vários envios.** Cada envio cria assignments novos, mesmo que o AssignmentID ou
um problema se repita, para manter a importação simples. Juntar ou substituir envios fica para
quando houver uma entidade de dataset.

**O zip do professor não é confiável.** O nome de cada arquivo é confinado ao diretório de destino
antes de escrever, e a mensagem de erro não repete o caminho, que pode carregar conteúdo do aluno.
O teto contra zip-bomb conta os bytes realmente descomprimidos, porque o tamanho declarado no zip
é controlado por quem o mandou.

**O dado limpo volta do banco com os mesmos tipos e na mesma ordem.** O treino ordena por
`submitted_at` e o `ml/` compara ids, então um id que voltasse como texto ou um horário sem fuso
mudaria o resultado numérico sem erro. A partição do treino lista os alunos na ordem das linhas,
então a ordem do arquivo também tem de sobreviver à importação e ao banco. Por isso o teste do
repositório compara com `assert_frame_equal` em dtype estrito, e o teste da importação confere a
ordem.

**O aviso de poucos alunos conta todo aluno com `Run.Program`.** O `trainability_check` espelha a
partição do treino, que não filtra os alunos com menos de três execuções, porque um aluno não
sai da análise por ter feito pouco do exercício. O espelho é escrito à mão, porque o domínio da
importação não pode importar o `ml/`.

## Problemas

**A chave de `problem` é (`assignment_id`, `problem_id`).** O `ProblemID` do dataset só é único
dentro do assignment, e sem um id próprio do banco a `submission` e a `problem_kc` continuaram com o
`problem_id` que já tinham, sem renumerar nada.

**Quem junta problema e KC é `knowledge_components`.** A chave estrangeira vai da `problem_kc`
para `problem`, então o problema não sabe quais KCs apontam para ele, e a entidade `Problem` não
carrega KCs. A rota `/assignments/{assignment_id}/problems/knowledge-components` fica na
`presentation/` de `problems`, mas a lógica dela é um use case de `knowledge_components`. Fazer
`problems` buscar os KCs criaria um ciclo entre as duas funcionalidades.

**A aplicação não fala em Q-matrix.** Na literatura, a Q-matrix é a matriz problema × KC, e é isso
que o `ml/` monta. A aplicação nunca devolve uma matriz, e sim os KCs ligados a cada problema. Por
isso a entidade, a tabela (`problem_kc`) e as rotas dizem o que guardam, e o termo da literatura
fica só no `ml/` e nas etapas do KCGen-KT.

**Um KC novo só liga problemas do próprio assignment.** Antes da FK, um `problem_id` qualquer era
aceito em silêncio. Com ela, viraria um erro do banco (500). A regra recusa o pedido antes, com a
lista dos problemas que não existem.

**A descrição deduzida pelo LLM deixa de ser gravada.** Ela era uma etapa do TCC 1 que o paper não
tem, e o enunciado, quando o pacote o traz, toma o lugar dela (a descrição e o enunciado, nas linhas
11 e 14 do KCGen-KT no `DEVELOPMENT.md`).
A coluna `description` e as rotas que a devolvem continuam até a tela Conceitos, que as troca pelo
enunciado. As descrições já gravadas das turmas antigas ficam como estão.

## Remoção

**Remover é soft delete, para guardar o histórico.** O KC e o vínculo removidos continuam no banco,
com `deleted_at`. Não há rota de restaurar: o histórico serve para saber o que o professor mudou, e
desfazer um vínculo é ligar de novo.

**O índice único de `problem_kc` vale só para os vínculos ativos.** Sem isso, religar um vínculo
removido esbarraria na linha antiga. Com o índice parcial, a linha antiga fica como histórico e
nasce uma nova, então cada remoção e cada religação ficam registradas.

**A fusão também guarda o histórico.** Antes ela reescrevia o `kc_id` dos vínculos do KC descartado.
Agora ela cria os vínculos que faltam no KC que fica e marca os do descartado como removidos.

**Um KC que perde o último problema sai junto.** Um KC sem problema não entra no treino nem no
dashboard, e com soft delete isso é reversível.

**Depois do treino não há remoção de KC.** Um modelo publicado prevê os conceitos que conheceu, e
a edição é recusada em `trained` (ver Dashboard), então o dashboard nunca precisa do nome de um KC
removido.

## Dashboard

**A tela entrega o dado, não a interpretação.** Saíram os níveis de aluno ("em risco"), os KCs
"críticos", as recomendações de reforço e as faixas de domínio (0,40 / 0,70). Cada uma era uma
inferência do app sobre um número que o modelo não sustenta como veredito. O professor recebe as
listas ordenáveis, a distribuição dos alunos em dez faixas de 10 pontos e decide sozinho.

**O que aconteceu e o que o modelo prevê ficam em blocos separados, nunca na mesma régua.** A taxa
de acerto observada é uma frequência; o domínio previsto é uma estimativa condicional ao histórico,
ancorada na taxa-base da turma. Comparar os dois de olho, entre blocos, é leitura do professor.
Colocar os dois na mesma barra diria "o modelo errou por x pontos", que não é o que a diferença
significa.

**O domínio é lido do vetor do último passo do Code-DKT.** É o estado atual do aluno, com todas as
tentativas, para todos os problemas do exercício, inclusive os que ele nunca tentou (Piech et al.
2015 leem a saída do DKT assim). Antes o app pegava, por problema tentado, a previsão feita um
passo antes da última tentativa. Não foi uma decisão, foi consequência de reaproveitar a saída da
avaliação (`predict_code_dkt`, uma linha por tentativa, que o AUC precisa). As duas leituras agora
são funções distintas, e a de avaliação não muda.

**A matriz é gravada por aluno × problema; o conceito é derivado na leitura.** O modelo prevê por
problema; o domínio por conceito é a média dos problemas que o exigem, pela Q-matrix. Gravar só a
matriz por problema (como o modelo prevê) mantém uma fonte de verdade e libera a tela de problemas
por domínio previsto. A média por conceito custa dez números por aluno.

**Os conceitos de um exercício treinado não mudam.** Sem re-treino, editar um KC depois do treino
mudaria o domínio derivado de um modelo já publicado. Qualquer edição em `trained` é recusada, e
com isso a Q-matrix dos vínculos ativos é a que o modelo conheceu, sem snapshot nem nomes "incluindo
removidos".

**A matriz de mastery é calculada uma vez por versão.** A versão publicada é resolvida uma vez por
chamada, para não misturar versões se um treino publicar no meio. A inferência usa o mesmo recorte
do treino. A gravação é numa transação, porque a checagem de "já calculado" só vê se existe alguma
linha, e uma matriz parcial seria servida para sempre. O cálculo continua na primeira leitura, não
no treino, porque a diferença para o professor são segundos e o worker fica mais simples.

**A métrica observada é a taxa de acerto em todas as execuções.** A 1ª tentativa é a métrica para
avaliar modelos; aqui o modelo está sendo aplicado. "Tentativas até completar" é a mediana, para o
aluno que tentou 68 vezes não puxar o número, sem outro tratamento de outlier.

**As estatísticas das execuções leem o dado inteiro.** Ao contrário do treino, elas incluem os
`Compile.Error`, porque os erros de compilação por execução dependem deles.

**A taxa de erro de compilação é `Compile.Error` / `Run.Program`.** E não `Compile.Error` /
(`Compile.Error` + `Run.Program`), que mistura os dois tipos de evento no denominador e varia com o
ritmo de tentativas de cada aluno. Pode passar de 1, e a tela diz "por execução".

**A lista de alunos vem inteira, sem paginação.** O teto é a turma (386 no CSEDM), a resposta fica
em dezenas de KB, e as colunas ordenáveis são calculadas, o que tornaria a ordenação no servidor
cara à toa. A lista é leve; o detalhe do aluno é outra rota, chamada ao clicar.

**O AUC não vai para a tela.** Fica no banco e no teste de regressão, que detecta mudança de
comportamento do código. Para o professor, o cartão do modelo diz versão, data e cobertura.

## Trava de job e infraestrutura

**A trava só é liberada quando o dono morreu.** O critério é o PID não existir mais, nunca o tempo
nem "o web reiniciou". Com `--reload`, o web reinicia e o treino sobrevive, e liberar a trava ali
deixaria um segundo treino entrar na mesma GPU de 6 GB.

**Quem pega a trava é o subprocess.** É o primeiro ato do worker, para o PID dono ser o de quem pode
morrer no meio. O pré-check no web é barato e não autoritativo, porque dois pedidos em paralelo
passam por ele e o segundo perde no subprocess.

**`release()` confere o dono.** O `UPDATE` tem `WHERE holder_pid = ?`, para um release tardio de
quem já perdeu a trava não soltar a de outro job.

**`AnotherJobRunning` não é regra de negócio.** É uma condição de corrida (race condition), não
defeito do pedido. Tratá-la como regra sugeriria que a exclusão mora no web e convidaria a apagar o
acquire do subprocess.

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

**`connect()` usa `check_same_thread=False`.** O FastAPI abre a conexão da requisição (a
dependência) numa thread do pool e roda a rota em outra. Com uma requisição por vez o pool costuma
reusar a mesma thread, e com duas em paralelo o `sqlite3` recusava a conexão e a api respondia 500.
É seguro porque cada requisição tem a própria conexão e a usa em sequência, nunca em duas threads
ao mesmo tempo, e o escritor continua único.

**O CLI do Claude é montado pelo link `~/.local/bin/claude`.** A montagem antiga apontava para uma
versão fixa em `~/.local/share/claude/versions/`. Quando o CLI se atualizou e apagou aquela versão,
o Docker criou uma pasta vazia no lugar, e toda geração de KCs passou a falhar com `Permission
denied`. O link é o que o próprio CLI mantém apontando para a versão atual, e o Docker o resolve ao
subir o container.

**O `vocab.pkl` é lido com `pickle` sem restrição.** Por isso o diretório da versão, que vem do
banco, é confinado ao `models/` da turma antes de abrir o arquivo. Um diretório adulterado viraria
execução de código.

**`CodeSnapshotId` é validado por allowlist.** É o único id do dataset do professor que vira nome de
arquivo, e aceita só letras, números e `._-`.

**O nome da turma é único, comparado pelo `ClassroomSlug`.** "Turma 6" e "turma  6" são a mesma
turma. O slug não vira mais caminho; o nome do zip de cada envio passa pela mesma limpeza
(`text_to_slug`) antes de virar o nome da pasta, porque ele vem do usuário.

**`ProgSnapAssignmentId` é um tipo próprio.** O assignment tem dois ids inteiros, o do banco e o do
dataset, e eles já foram trocados um pelo outro.

## Frontend

**A rota mora no hash da URL, sem biblioteca de rotas.** Um hook de poucas linhas lê o
`location.hash` com `useSyncExternalStore`. Com o hash, um F5 e o voltar do navegador funcionam, o
que um estado no `App` não daria. O react-router e o TanStack Router trariam loaders e rotas
aninhadas que o app não usa. Se um dia precisar, trocar é mecânico.

**CSS puro, sem Tailwind nem shadcn.** Um guia de frontend externo ao repositório (o do trabalho do
autor) parte dessa stack, mas o que ele quer garantir (nenhuma cor no ponto de uso, variante com
situação de uso) vale do mesmo jeito com tokens e uma prop `variant` que escolhe a classe. Trocar o
jeito de escrever CSS no meio do caminho custaria mais do que rende.

**O `<dialog>` nativo no lugar do Radix.** Ele já prende o foco, fecha no Esc e escurece o fundo.
Abrir como modal exige chamar `showModal()`, e esse é o único effect das primitivas, porque
sincroniza com uma API do DOM. O conteúdo só existe com o diálogo aberto, então o formulário nasce
limpo a cada abertura, por remontagem, sem precisar do Radix.

**Sem react-hook-form nem zod.** Os formulários das telas planejadas têm um campo cada, e o backend
já valida (tamanho do nome e nome único, com o 409). O `useState` resolve.

**`eslint-plugin-react` com o ESLint 10.** A versão 7.37.5 declara suporte só até o 9, mas as duas
regras que interessam (`no-unstable-nested-components` e `jsx-key`) foram testadas no 10 e
funcionam. O `.npmrc` já relaxa os peers por causa do `openapi-typescript`.

**As fronteiras entre camadas são um teste, e não uma regra do ESLint.** Com imports relativos, o
`no-restricted-imports` não distingue `../../components/ui` de `../../classrooms/components`. O
`architecture.test.ts` resolve o caminho real, como o `architecture_test.py` faz no backend.

**O `PageHeader` nasceu antes da terceira cópia.** A regra dos três é promover um padrão a
componente compartilhado na terceira ocorrência, mas toda página do desenho abre com o mesmo
cabeçalho, então ele nasce como componente compartilhado, pelo mesmo motivo dos quatro estados de
toda tela (carregando, erro, vazio e conteúdo, descritos no `ARCHITECTURE.md`).

**A importação recusa o pacote sem `CodeStates.csv` antes de processar.** O upload já diz o que
veio no zip, e sem o código dos alunos não há como extrair conceitos nem treinar. Recusar ali poupa
o professor de esperar o processamento para descobrir o que falta.

**Toda falha do upload vira a mesma mensagem, por enquanto.** Um zip corrompido, um zip bomb e um
path traversal chegam hoje como 500, porque o controller não trata o `BadZipFile` nem os
`ValueError` do extrator, e a tela não distingue isso de uma api fora do ar. Quando o controller
devolver um 400 com `detail`, a tela passa a separar os dois casos. O limite de 512 MB é conferido
na tela, antes de enviar.

**Os avisos da importação ganham um título na tela.** As mensagens do backend são técnicas e o
DTO descarta o `count` e o `location`, então a tela dá um título em pt-BR a cada código conhecido e
mostra a mensagem como veio. Por isso um aviso de viabilidade ainda não diz de qual exercício é.

**Um segundo envio para a mesma turma segue, com aviso.** O backend cria exercícios novos em vez de
substituir, e a tela avisa isso antes de processar, sem impedir.

**A lista de conceitos do exercício sai invertendo a de problemas.** A tela de conceitos pede só
`GET /assignments/{id}/problems/knowledge-components` e calcula quais problemas cada conceito
marca. Pedir também `GET /knowledge-components` seria guardar o mesmo dado duas vezes, e as duas
cópias poderiam discordar entre uma edição e a recarga.

**O exercício treinado mostra os conceitos só para consulta.** Os conceitos de um exercício
treinado ficam congelados, e o backend também recusa a edição, porque passariam a divergir dos que
o modelo publicado usa.

**A tela recusa deixar um problema sem conceito antes de chamar a api.** Os problemas e os conceitos
de cada um já estão na tela, então ela sabe qual problema ficaria vazio e diz o número dele. O
backend continua barrando, e se barrar mesmo assim, a mensagem dele aparece.

**O xis só confirma quando o conceito sairia do exercício junto.** Tirar um conceito de um problema
que continua marcado por ele em outros é rápido e fácil de refazer. Tirar do último problema remove
o conceito, e sem restaurar.

**O diálogo de extração não fecha enquanto o job roda.** Como reencontrar uma extração em andamento
ficou fora do escopo, fechar perderia o acompanhamento. O Esc é bloqueado, o `Dialog` reabre se o
navegador o fechar mesmo assim (o Chrome fecha no segundo Esc) e a aba pede confirmação antes de
sair. A tela mostra os estágios que o job informa, com a contagem do estágio atual.

**A barra de ação e o `OutcomeMessage` subiram para `components/`.** Uma funcionalidade não importa
os componentes de outra, e a importação e os conceitos precisavam dos dois. Na versão 5 do design
(`DESIGN.md`), a barra de ação sai do app, e a migração para esse design (`IMPLEMENTATION_PLAN.md`)
remove o `PageActionBar`.

**Uma recarga que falha mantém o que já estava na tela.** O `QueryStates` só mostra o erro quando
ainda não há dado; uma falha transitória numa recarga em segundo plano não apaga uma lista que
estava certa.

**O contexto mora no endereço, e a navegação é um menu em árvore com breadcrumb.** Turma e
exercício entram na rota (`/classrooms/:classroomId/assignments/:assignmentId/analysis`), então um
F5 ou um link abrem no lugar certo e nenhuma tela precisa de seletor. Das opções desenhadas, o menu
em árvore com o caminho no topo foi o que deixou claro onde o professor está sem ocupar a tela.

**No menu, escolher uma linha só navega, e o botão de mais e menos na ponta abre e fecha.** Quando o
clique também abria, uma linha já aberta fechava ao ser escolhida, e a tela Turmas abria no menu a
mesma lista que já mostra. A única abertura automática é a de uma tela de exercício, para a linha
atual aparecer marcada. O que fica aberto é lembrado no navegador.

**As tabelas da Análise seguem o estilo das tabelas acadêmicas.** Um traço escuro sob os rótulos e
no fim, nenhum vertical e nenhum traço acima dos rótulos, sem seguir a ABNT à risca. A legenda
numerada e a fonte abaixo da tabela não entraram, para não destoar do resto do app. Os números ficam
centralizados sob os rótulos, que também são centralizados. À direita, a convenção de tabela de
dados, pesa pouco com números curtos e o "355 de 386" desalinha de qualquer jeito, e à esquerda o
valor cola na coluna anterior. A tabela usa Arial, a fonte de dados do app.

**O app passou a ser formal e cinza, e o azul ficou só com o modelo.** Antes da versão 1 do
`DESIGN.md`, o azul de ação estava no botão primário, no menu, nas abas e nos links, e um azul quase
igual pintava o domínio previsto. O professor via a mesma cor no botão e no dado sem que um tivesse
a ver com o outro. Com a interface em cinza, o azul passa a ser a única cor que diz alguma coisa,
que um modelo produziu o dado, e o olho vai para ele sem legenda. Na versão 4 do design a regra
passou a valer para os dois modelos do app, o Code-DKT e o modelo de linguagem, e o ícone diz qual.
As referências foram o Carbon (componentes e gráficos), o padrão de gráfico do gov.br (título,
subtítulo e fonte na figura) e o Distill (o tom acadêmico), comparadas em três iterações de design
registradas no `DESIGN.md`.

**A paleta tem três papéis, sem verde nem âmbar.** Cinza para a interface, azul para o modelo e
vermelho para erro e exclusão. O verde e o âmbar existiam para as faixas de domínio, que saíram com
a decisão de entregar o dado. Um sucesso verde seria uma cor a mais só para dizer "deu certo", e o
ícone de ✓ já diz isso.

**O observado é cinza 80 e não preto puro.** O preto `#161616` é também o texto e o traço da
tabela, e a barra de 10px ao lado dos nomes em negrito deixava a linha pesada. O `#393939` ainda
lê como preto e separa bem do azul, inclusive para daltonismo.

**Raio 0 em tudo, e sombra só no que é objeto.** As barras quadradas, os botões e os gráficos
vieram do Carbon, e manter os 2px nos cartões e no menu deixaria dois raios convivendo. A sombra
fica no cartão, no diálogo e na barra superior, para separar objetos do fundo, e nada dentro deles
tem sombra, para ela continuar querendo dizer "isto é um objeto".

**Duas fontes, cada uma com um papel, a Public Sans na interface e o Arial nos dados.** O app já
separava uma fonte de dados (a mono, para contagem, percentual, data e identificador), e o Arial
assume esse papel e ganha a tabela e o gráfico inteiros. O motivo é o tom e a monografia, que está
em Arial, então tabelas e figuras capturadas do app entram no texto sem destoar. A Open Sans saiu
porque a Public Sans é mais sóbria na interface. Duas sem serifa parecidas só funcionam com a
fronteira nítida, por isso a regra é por papel e não por gosto, e uma etiqueta com número continua
inteira em Public Sans. No Linux o Arial cai na Liberation Sans, que tem as mesmas medidas, e o
layout não muda. A serifa nos títulos foi testada e descartada.

**A linha e o cabeçalho de tabela têm 32px.** É a densidade compacta do Carbon, e o professor vê
mais alunos sem rolar. O cabeçalho com a mesma altura das linhas deixa a tabela com um ritmo só, e
um rótulo longo trunca com o texto inteiro no hover, em vez de quebrar em duas linhas. O histograma
da tabela perdeu o eixo para caber nos 32px, e a escala de 0 a 100% está na dica do cabeçalho.

**Os estágios da extração e do treino são azuis.** A lista de estágios serve a dois diálogos, e os
dois são trabalho de modelo, o modelo de linguagem na extração de conceitos e o Code-DKT no treino.
Até a versão 3 do design a extração ficava preta, porque o azul era só do Code-DKT. Com as estrelas
distinguindo o modelo de linguagem pelo desenho, o azul passou a valer para os dois.

**O ícone do capelo (chapéu de formatura) da barra superior é preto.** Ele é a marca do app e não
fala do modelo, então não pode ser azul pela regra.

**As dicas de hover são um componente, e não o `title` nativo.** O navegador espera perto de um
segundo antes de mostrar o `title`, e isso não se configura. O `Tooltip` aparece no hover ou no
foco, fixo na janela para não ser cortado pela rolagem da tabela, e o leitor de tela continua lendo
o `aria-label`.

**A janela não rola, só o conteúdo.** A barra superior e o menu ficam parados sem `sticky`, que
pediria a barra sticky também. A tabela oculta do histograma, que dá os números ao leitor de tela,
fica dentro de um `div` escondido, porque uma tabela ignora o `clip` do `visually-hidden` e esticava
a página centenas de pixels.

**O Chart.js desenha só a curva de perda.** As barras e os histogramas das tabelas são CSS, porque
são dezenas por tela e um canvas para cada seria pesado sem ganho. No teste, o `react-chartjs-2` é
trocado por um componente vazio, porque o jsdom não tem canvas, e o teste lê a tabela oculta ao lado
do gráfico.

**O diálogo de treino repete o da extração, e a lista de estágios virou um componente.** Três
estágios, a época atual e a curva de perda ao vivo, sem fechar enquanto o job roda. Ao terminar, a
curva é buscada uma última vez, porque as épocas finais caem depois da última consulta. O AUC não
aparece, pela decisão do dashboard, e a fração do código lida pelo parser Java aparece como um dado
da qualidade do treino.

**A nota do rodapé da Análise só explica o marcador.** Fonte e versão do modelo saíram, e a nota
diz em uma frase que o cérebro marca os dados estimados pelo modelo. Ela só aparece com modelo
treinado, quando há colunas marcadas.

**Uma figura só entra com um dado que a tabela não tem.** Uma visão geral por problema e os
pequenos múltiplos da distribuição por conceito foram desenhados e saíram, porque redesenhavam os
números das tabelas. A figura da Análise é a curva de aprendizagem, que mostra a ordem das
tentativas, uma dimensão que nenhuma tabela tem.

**A curva de aprendizagem usa a taxa de erro por oportunidade.** É a convenção do PSLC DataShop e
da literatura de KCs, então a banca lê a curva caindo como aprendizado sem explicação. A oportunidade
é cada execução do aluno num problema que exige o conceito. Quem acerta para de praticar, e nas
oportunidades altas sobram os alunos com dificuldade, o que faz o fim da curva subir. Por isso a
curva para quando menos de 10% da turma chega à oportunidade.

**A curva de aprendizagem tem dois eixos, uma exceção consciente.** Dois eixos costumam enganar,
porque o cruzamento entre as séries depende só das escalas escolhidas. Aqui os alunos em cada
oportunidade são contexto da taxa de erro, e não uma medida para comparar com ela. Juntos no mesmo
gráfico, eles mostram por que o fim da curva sobe. Para não confundir, as barras ficam atrás e
apagadas, cada eixo leva a cor e o título da sua série, e a legenda diz qual eixo é de qual.

**A linha de fatos substitui a descrição da Análise.** A frase fixa era igual em todo exercício. A
linha diz alunos, problemas, conceitos, execuções e a versão do modelo com a data do treino, e com
isso volta o que o cartão do modelo decidido para o dashboard dizia e que nunca chegou à tela. A
etiqueta de situação saiu do caminho, que só navega, e foi para o lado do título.

**Conceitos é a primeira aba da Análise.** A pergunta central do app é quais conceitos a turma ainda
não domina. A ordem padrão dentro da aba continua sendo a taxa de acerto.

**Observado e modelo se distinguem pela cor e pelo cérebro, sem mais nada.** Um cabeçalho agrupado
("O que aconteceu" e "O que o modelo prevê") e uma linha fixa da turma foram desenhados e saíram. O
cabeçalho repetia o que a cor e o marcador já dizem, e a linha da turma ficava vazia nas colunas que
não têm um total que faça sentido, como os alunos que completaram.

**O detalhe do aluno continua no diálogo.** Um painel lateral que empurra a tabela foi desenhado e
ficou para depois. Com ele aberto, as etiquetas de "Conceitos mais fracos" ficavam cortadas demais.

**O menu recolhe em tela estreita.** Abaixo de 900px ele fica atrás de um botão da barra superior e
abre por cima do conteúdo. O menu fixo de 260px espremia a Análise numa faixa ilegível no celular.

**Os exercícios da turma são uma tabela, e não cartões.** São itens do mesmo tipo com os mesmos
atributos, e os cartões com borda dentro do cartão com sombra quebravam a regra de que a sombra marca
objeto. A tabela também deixa ler juntas colunas que nenhuma tela mostrava, como os alunos por
exercício, que caem de 386 para 306 ao longo do semestre na CSEDM.

**Cada exercício tem um botão de próximo passo, escolhido pela situação.** Com dois links fixos, o
professor tinha de adivinhar qual tela abrir. O botão diz a ação que a situação pede e leva o ícone
da tela de destino. É orientação de fluxo, não interpretação de dado, e Conceitos e Análise continuam
no menu.

**A lista de alunos da turma é paginada, ao contrário da Análise.** A Análise lista os alunos de um
exercício, e a lista leve cabe inteira. A turma soma todos os exercícios e cresce com o semestre, e
dez por página com busca pelo identificador mantém a tela curta.

**O domínio do aluno na turma é a média dos exercícios treinados.** Com um exercício treinado ele é o
domínio desse exercício. Com vários, a média mistura modelos treinados sobre dados diferentes, e a
dica da coluna diz isso. Quem não fez nenhum exercício treinado mostra "sem modelo".

**A figura de execuções por dia é a figura da turma.** Ela mostra o ritmo dentro de cada janela de
exercício, que a tabela não tem, como a concentração no fim do prazo. Funciona com qualquer
ProgSnap2, porque o `ServerTimestamp` é obrigatório na importação, com quatro regras para dados
diferentes da CSEDM. A agregação vira semanal acima de cerca de 120 dias, os rótulos de janelas que
se sobrepõem empilham em até três faixas, o eixo fica limitado às janelas para uma data errada não
esticá-lo, e o dia segue o `ServerTimezone`, que a importação ainda precisa passar a ler.

**A atividade recente mostra treinos e extrações de conceitos.** Com só as turmas criadas, a lista
não dizia nada que a tabela ao lado não mostrasse. Os eventos que o professor provocou (dados
importados, conceitos extraídos, modelo treinado) contam o que aconteceu desde a última visita.

**Os ícones têm um significado só.** Blocos são Conceitos, código são Problemas, o cérebro é o
Code-DKT, no marcador de estimado e na etiqueta Treinado, e as estrelas são o modelo de linguagem.
O cérebro com circuito foi comparado e descartado, porque em 13px perde a legibilidade. A lista,
cogitada para Conceitos, ficaria parecida com o ícone de Problemas. As etiquetas de situação levam o
ícone da etapa, mas o menu mantém o ponto vazio, meio ou cheio, para a lista longa de exercícios
ficar discreta.

**A tela Turmas não soma alunos.** Duas turmas podem ser recortes do mesmo dado, como a Turma teste,
e a soma contaria o mesmo aluno duas vezes.

**No Linux, o Arial das tabelas cai na Liberation Sans.** O Fedora não tem o Arial, e a licença não
permite servi-lo pela web. A Liberation Sans tem as mesmas medidas, então o layout não muda, só o
desenho de alguns caracteres. Capturas feitas no nitro saem nela.

**A tela Conceitos é uma matriz problema × conceito.** As duas vistas que a tela tinha, os conceitos
de cada problema e a lista de conceitos, eram a mesma informação desenhada duas vezes, numa página
longa de etiquetas com xis. A matriz é a Q-matrix da literatura, cabe numa tela com 15 conceitos e
10 problemas e mostra nas margens a recorrência de cada conceito e quantos conceitos cada problema
tem. No código ela continua sendo os vínculos problema × conceito. A lista de problemas, com o
enunciado quando o pacote o traz, fica numa segunda aba, como as abas da Análise.

**Mesclar conceitos saiu.** Com dois conceitos duplicados, o professor remove um e o outro fica, e
isso é mais simples de entender do que um diálogo de mescla.

**A origem do conceito mostra as soluções que o modelo de linguagem leu e onde o conceito aparece
nelas.** O professor precisa ver de onde o conceito veio para validá-lo, e a evidência é o código.
Não há como medir a influência de cada linha num modelo acessado pela CLI, então os trechos vêm de
uma chamada separada, depois do agrupamento e na mesma extração, com o prompt do Duan intacto, e a
tela os mostra como o lugar onde o conceito aparece, e não como a causa dele (O que o app acrescenta
ao KCGen-KT, no `DEVELOPMENT.md`). As frases candidatas do modelo, as justificativas de cada KC,
foram desenhadas antes e saíram, porque repetiam o nome do conceito com outras palavras. Elas passam
a ser guardadas e traduzidas, e a tela Conceitos decide como mostrá-las, tendo em conta que o
desenho anterior as achou repetitivas.

**A fonte mono volta, só em bloco de código.** O sistema tem duas fontes com papéis fixos, e o código
é a exceção, porque a indentação e o alinhamento dependem da largura fixa. Fora do bloco de código,
números e identificadores continuam em Arial.

**A dica é o ?, e o ! fica para alerta.** O mesmo círculo com ! marcava uma explicação em cinza e um
problema em vermelho, e o professor não tinha como saber qual dos dois estava vendo antes de ler.

**A linha de fatos separa os itens por vírgula.** O ponto médio parecia ponto final, e um traço
vertical foi testado e pesou demais. A vírgula lê como frase.

**O que o modelo de linguagem escreveu leva as estrelas, e não o texto em azul.** O nome do conceito
vem do modelo. Pintar o texto de azul encheria as telas, porque o nome do conceito aparece em toda
parte, e cansaria a leitura em tabela densa. O marcador no fim do texto diz a origem sem esses
custos. Quando o professor renomeia um conceito, o nome passa a ser dele e o marcador some, o que
pede o app registrar se o nome foi editado.

**Aprovar conceitos fica na faixa das abas.** A barra fixa no rodapé era o único lugar do app com uma
ação presa à janela. Ao lado de Novo conceito, na aba da matriz, o Aprovar fica junto do que ele
aprova, e desabilitado enquanto houver problema sem conceito.

**O app não tem barra fixa presa à janela.** A barra de ação no rodapé existia na importação e nos
conceitos. Ela separava os botões do que eles enviam e ficava sobre o conteúdo. As ações de um
formulário passam para o rodapé do cartão, junto dos campos, e as da tela para o cabeçalho ou a faixa
das abas.

**Os requisitos do pacote ocupam a coluna das caixas vazias.** Antes do processamento, o resumo dos
dados mostrava quatro caixas cinzas sem número, que não diziam nada. A coluna passa a listar o que o
pacote precisa ter, e depois do envio cada requisito ganha o visto ou o xis. A lista "O que veio no
pacote" deixa de existir como bloco à parte, porque o requisito já diz o arquivo que o atendeu.

**A altura da importação não muda entre os passos.** A caixa do pacote tem 104px na área de soltar,
com o arquivo e na recusa, e os dois cartões do passo 1 têm sempre a mesma altura, cada um com o seu
rodapé. Uma caixa de processamento que aparecia e sumia e a mensagem de recusa longa faziam a tela
pular a cada passo.

**O resultado da importação reusa a tabela de exercícios da Turma.** Os quatro números grandes viram
a linha de fatos, e a tabela Exercício | Situação vira a mesma tabela da Turma, com período, alunos,
execuções, taxa de acerto e o próximo passo. O professor vê o que foi importado no formato em que vai
encontrar depois, e a tela não ganha um componente só dela.

**Os ajustes da importação ficam neutros.** Compilações repetidas descartadas e poucos alunos num
exercício não impedem a gravação, e o app não tem âmbar para um meio-termo. Uma lista neutra, com
título e detalhe, registra o que o sistema corrigiu sozinho, e o vermelho fica para a recusa.

**Os ícones do cartão ficam só no título.** "Turma e arquivo" leva as pessoas e a pasta juntas antes
do texto, e os rótulos dos campos logo abaixo ficam sem ícone, para o mesmo sinal não aparecer duas
vezes seguidas. A pasta é a simples, e a pasta compactada foi testada e descartada.

