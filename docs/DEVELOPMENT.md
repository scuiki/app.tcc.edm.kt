# Desenvolvimento

Como o app implementa os métodos da literatura em que se apoia, onde difere deles e por quê. Cada
item compara o paper, o repositório oficial dos autores, o TCC 1 e o app, com a decisão tomada e o
estado dela. É a base para descrever, no artigo, o que o desenvolvimento fez em relação a cada
método. As decisões de engenharia continuam no `DECISIONS.md`.

## Code-DKT

### Fontes

- **Paper.** Shi et al. (2022), nos anais do EDM 2022, pp. 50 a 61. As páginas citadas são as dos
  anais, com a do PDF entre parênteses. A página do PDF é a dos anais menos 49.
- **Repositório oficial.** [YangAzure/Code-DKT](https://github.com/YangAzure/Code-DKT), commit
  `8ddd13e`. Os arquivos e as linhas citados são desse commit. Um caminho `src/` sem indicação é
  desse repositório, e os do TCC 1, do app e do code2vec vêm marcados.
- **App.** As linhas do app citadas, marcadas como "do app", são do commit `eb95fa0`, de antes da
  implementação. O plano que leva as decisões ao código está no `CODE_DKT_PLAN.md`.
- **Padrões citados pelo paper.** Para o que não especifica, o paper diz "All other parameters were
  defaulted as the original settings of code2vec and DKT" (p. 55 (PDF 6)). O code2vec é Alon et al.
  (2019), com o repositório [tech-srl/code2vec](https://github.com/tech-srl/code2vec), commit
  `77637c5`. O DKT é Piech et al. (2015).
- **TCC 1.** [scuiki/tcc.edm.kt](https://github.com/scuiki/tcc.edm.kt), commit `0e8807c`, com os
  notebooks `06_code_dkt.ipynb`, `07_comparison.ipynb` e `08_multirun_regeneration.ipynb` e os
  módulos de `src/` de onde o código do app foi portado. São o modelo, o treino e a previsão
  (`src/models/code_dkt.py`), a perda (`src/models/dkt.py`), os AST paths e os tensores de entrada
  (`src/code_features.py`), as sequências e a partição (`src/data_loader.py`) e o índice de
  problemas e o AUC (`src/evaluation.py`). As células dos notebooks são contadas pela posição no
  arquivo, a partir do 0 e incluindo as de texto, e não pelo número de execução que o Jupyter mostra.

### Critério

Quando as fontes discordam, a decisão segue esta ordem.

1. O que o paper especifica vale o paper.
2. Quando a equação do paper contradiz o texto do próprio paper, vale o texto, com o repositório
   como evidência de como os autores implementaram.
3. O que o paper não especifica vale o repositório oficial, que é o código publicado pelos autores.
   Onde os padrões do code2vec e do DKT diferem do repositório, também vale o repositório.
4. Onde o repositório tem um defeito, como deixar o futuro entrar na previsão ou deixar o acaso
   ligado na avaliação, vale o paper ou a prática estabelecida, e a correção fica registrada.
5. O que nenhum dos dois define é decisão do app, registrada aqui.

### Seção 3 do paper, o modelo

#### O que ficou igual

Estes pontos são iguais no repositório e no app, e também no paper quando ele trata deles. Não
pediram decisão.

- O problema faz o papel do KC, "We use problemIDs for KCs in this work" (p. 52 (PDF 3), nota 1).
- O modelo prevê a próxima tentativa, e só a saída do próximo problema entra no treino e na
  avaliação (p. 53 (PDF 4)).
- A entrada do DKT é o one-hot de tamanho 2M, com a posição q_t + M(1 − a_t) ligada (p. 53 (PDF 4)).
- O LSTM, que o paper usa no lugar do RNN simples, tem uma camada, como no repositório
  (`src/config.py:9`). O estado começa zerado (p. 53 (PDF 4)) na primeira posição da sequência de 50,
  e quem tem menos de 50 execuções só chega à primeira execução depois do padding à esquerda (ver a
  linha 20).
- Os paths vão de folha a folha na AST, como no code2vec (p. 53 (PDF 4)). O parser é o javalang, e
  os limites de 8 de comprimento e 2 de largura vêm do repositório (`src/config.py:12-13`), com os
  mesmos valores do code2vec (`preprocess.sh:42-48` do repositório dele). O repositório conta o
  comprimento em nós, com as duas folhas incluídas (`src/path_extractor.py:59` e `147`), e o
  code2vec conta em arestas (`JavaExtractor/JPredict/src/main/java/JavaExtractor/FeatureExtractor.java:140-141`
  do repositório dele). Com o mesmo 8, o limite do repositório é um nó mais curto, e o app segue o
  repositório.
- Cada path tem o nó inicial, o caminho e o nó final, e as duas folhas fazem parte do caminho, como
  em input|method|body|String|value (p. 53 (PDF 4)).
- O embedding de nó é compartilhado entre o início e o fim do path, e o de path é separado, os dois
  com inicialização gaussiana (p. 54 (PDF 5)). Cada um tem 100 dimensões
  (`src/c2vRNNModel.py:14-15`), e os três somam os 300 do "embedding size of code feature
  extraction" (p. 55 (PDF 6)).
- O x_t entra em cada e_r e de novo na entrada do LSTM (p. 54 (PDF 5)).
- O dropout de 0,2 durante o treino cai em cada e_r inteiro, nos embeddings de nó e de path e também
  na cópia do x_t, e é esse e_r que entra na atenção e na soma ponderada. O x_t que vai direto para o
  LSTM fica sem dropout. Ele vem do repositório (`src/c2vRNNModel.py:16` e `52-54`), e o paper não
  fala dele.
- As soluções de que o extrator não tira nenhum path, porque o javalang não as lê ou porque nenhum
  path passa nos limites, entram no modelo sem paths, só com o acerto ou o erro. No TCC 1, 14,0% dos
  53.990 snapshots distintos dos cinco exercícios ficaram sem paths (notebook 06, célula 12), e numa
  amostra de 100 execuções do treino do A439 foram 25 (célula 8). O repositório faz o mesmo, e o
  paper não trata delas.
- O código concatena na ordem início, fim e path, e o paper escreve início, path e fim (p. 54
  (PDF 5)). A ordem muda só a posição dos números no vetor, e não o que o modelo consegue aprender.

#### As decisões

| # | Item | Paper | Repositório | TCC 1 | App antes | App depois |
|---|---|---|---|---|---|---|
| 1 | Quais paths entram | R amostrados aleatoriamente (p. 53), sem valor para R | os 100 primeiros, sem amostragem aleatória | 50 amostrados, seed 42 | 50 amostrados, seed 42 | 100 amostrados, seed 42 |
| 2 | Ordem dos modificadores Java | não trata | a do `set`, que muda a cada processo | igual ao repositório | igual ao repositório | igual ao repositório, com `PYTHONHASHSEED=0` |
| 3 | Token fora do vocabulário | não trata | índice próprio | o 0 do preenchimento | o 0 do preenchimento | índice próprio |
| 4 | Score da atenção | α = SoftMax(E·W_a) (p. 54) | camada com tanh antes do score | igual ao repositório | igual ao repositório | igual ao repositório |
| 5 | Eixo do softmax | os R paths (p. 54) | o tempo | os R paths | os R paths | os R paths |
| 6 | W_0 depois da soma ponderada | z = W_0(Σ α_i e_i) (p. 54) | não tem | não tem | não tem | incluído, quadrado, do tamanho de e_r (2M + 300), sem viés |
| 7 | Dropout na saída do LSTM | não trata | criado e nunca usado | 0 no padrão, 0,1 na grade | 0,1 | nenhum |
| 8 | Dropout dos embeddings na avaliação | não trata | ligado | desligado | desligado | desligado |

#### Justificativas

**1. Quais paths entram.** O paper representa cada solução por "R randomly selected code paths"
(p. 53 (PDF 4)) e não dá o valor de R. O repositório usa R=100 (`src/readdata.py:55`), mas pega os
100 primeiros da lista, sem amostragem aleatória (`src/readdata.py:140`). A lista segue a ordem em
que os pares de folhas são percorridos, primeiro todos os paths da primeira folha e depois os da
segunda. Assim, o corte nos 100 primeiros fica com o começo do método, da assinatura em diante, e
descarta o fim quando a solução tem mais de 100 paths. No A439 do TCC 1, a mediana era de 122 paths
por solução e o percentil 95 era de 268 (notebook 06, célula 8). O app segue o paper na amostragem
aleatória e o repositório no valor (critérios 1 e 3). O padrão do code2vec é 200 (`config.py:60` do
repositório dele), e pelo critério 3 vale o repositório. A seed 42 só fixa a amostragem aleatória, e
o valor é o do TCC 1 e do resto do app (critério 5). O TCC 1 usava R=50 e atribuía o valor à Tabela
3 do paper (notebook 06, célula 3, e `docs/code_dkt_implementation.md:175` do TCC 1), mas a Tabela 3
é o desempenho por problema (p. 56 (PDF 7)), e o conjunto de valores (30, 50, 100, 300) que ele cita
é o do número de features do TF-IDF de um baseline (p. 55 (PDF 6)).

**2. Ordem dos modificadores Java.** O javalang devolve os modificadores de uma declaração, como
`public` e `static`, num conjunto do Python, e o repositório transforma esse conjunto em lista com
`list(root)` (`src/path_extractor.py:28`). A ordem de um conjunto de textos depende da semente de
hash que o Python escolhe ao acaso a cada processo. Por isso uma solução com dois ou mais
modificadores na mesma declaração, como `public static`, gera paths diferentes em processos
diferentes, e com um modificador só a ordem não muda. No A439 essas soluções são raras, e mesmo
assim o first-attempt AUC alternava entre 0,7595 e 0,7608. O paper não trata do assunto, então o app
mantém o código do repositório (critério 3) e fixa a variável de ambiente `PYTHONHASHSEED=0` nas
imagens (critério 5). A ordem passa a ser sempre a mesma sem mudar o método, inclusive entre
reinícios do container e imagens novas, enquanto a versão do Python for a mesma, e a imagem fixa o
Python 3.11. Fixar o `PYTHONHASHSEED=0` tira da api a proteção contra hash flooding, um ataque que
manda chaves com o mesmo hash para travar o processo. O risco é desprezível, porque a api não
publica porta e o app tem um usuário numa rede privada.

**3. Token fora do vocabulário.** Um nó ou path que aparece no teste e não apareceu no treino
precisa de um índice. O repositório reserva o 0, que ele chama de END mas só usa como padding à
esquerda, e o 1 para o token desconhecido (UNK) (`src/readdata.py:18-19` e `138`). O TCC 1 e o app
usavam o 0 para os dois (`src/ml/code_dkt/model_input.py:22-24` do app), e o modelo não distinguia
uma posição de padding de um path desconhecido. No TCC 1, 6,0% dos paths do teste do A439 estavam
fora do vocabulário (notebook 06, célula 15). O app passa a seguir o repositório (critério 3).

**4. Score da atenção.** A equação do paper calcula o score de cada path como uma combinação linear
do vetor dele, α = SoftMax(E·W_a) (p. 54 (PDF 5)). O repositório passa o vetor antes por uma camada
linear com tanh e só então calcula o score (`src/c2vRNNModel.py:17-18` e `56-57`), como faz o
code2vec (`tensorflow_model.py:252-254` do repositório dele), de onde o paper diz que a estrutura
veio, "This initial structure is drawn from code2vec" (p. 53 (PDF 4)). A diferença importa porque
cada e_r carrega o x_t, que é o mesmo em todos os paths da mesma tentativa. Na versão linear, a parte
do score que vem do x_t é a mesma parcela somada a todos os scores, e o softmax não muda quando se
soma o mesmo valor a todos eles, então o acerto não influencia os pesos. Com o tanh, o x_t se
combina com o código de cada path antes do score. O paper chama esse passo de "Score-Attended Path
Selection" e diz que o e_r inclui o acerto (p. 54 (PDF 5)). Diz também que o Code-DKT "adds score to
the attention mechanism to assign weights to code paths", o que permite "to directly use score
information to select the most predictive code paths" (p. 52 (PDF 3)). Só a versão do repositório
faz isso. O app mantém a versão do repositório (critério 2), e a equação do paper é lida como uma
notação simplificada.

**5. Eixo do softmax.** O paper normaliza os scores sobre os R paths de cada tentativa, com a soma
de 1 a R no denominador (p. 54 (PDF 5)). O repositório usa `Softmax(dim=1)`
(`src/c2vRNNModel.py:21`) num tensor de forma (lote, tempo, paths, 1), o que normaliza sobre o
tempo. Assim a atenção de um passo depende dos passos seguintes do mesmo aluno, inclusive da
tentativa que o modelo deveria prever. O eixo 1 é provavelmente herança do code2vec, em que o tensor
não tem o tempo e o eixo 1 é o dos paths (`tensorflow_model.py:260` do repositório dele). O TCC 1 já
usava o eixo dos paths (`src/models/code_dkt.py:91-92` do TCC 1), e o app mantém (critério 4).

**6. W_0.** O paper multiplica a média ponderada dos paths por uma matriz W_0 para obter o vetor de
código z, e isso aparece no texto, na equação e na Figura 3, como "Linear Layer W_0" (p. 54 (PDF
5)). O repositório não tem essa camada e manda a média ponderada direto para o LSTM
(`src/c2vRNNModel.py:59-60`). O TCC 1 também não tem, e a documentação dele chamava de W_0 a camada
com tanh da atenção (`docs/code_dkt_implementation.md:320-321` do TCC 1), que é outra. O app inclui
o W_0 (critério 1) como uma camada linear quadrada, do tamanho de e_r, de 2M + 300 para 2M + 300,
que dá 320 nos exercícios de 10 problemas da CSEDM, porque o paper não dá o tamanho de z (critério
5). A camada é sem viés, porque o texto diz que a média ponderada "is then multiplied by a matrix
W0" e a equação é z = W_0(Σ α_i e_i) (critério 1). O "bias terms are omitted for simplicity" da p.
53 (PDF 4) fala só das duas equações do RNN, e não do W_0. A camada é criada no `__init__` depois
das camadas da atenção e antes do LSTM, e essa posição muda o consumo do gerador aleatório na
inicialização das camadas seguintes (critério 5). A primeira operação do LSTM sobre a entrada também
é linear, e duas operações lineares seguidas equivalem a uma. Por isso o W_0 não aumenta o que o
modelo consegue representar, e muda só o número de parâmetros e o caminho do treino.

**7. Dropout na saída do LSTM.** O paper não fala desse dropout. O repositório cria a camada com 0,1
(`src/c2vRNNModel.py:32`), mas a linha que a usaria está comentada (`src/c2vRNNModel.py:65-66`). O
DKT aplica dropout na passagem de h_t para a saída y_t, sem dar a taxa (Piech et al., 2015,
subseção Optimization), e pelo critério 3 vale o repositório, que desligou essa camada. O 0,1 do app
veio da melhor configuração da grade do TCC 1, que tinha dimensão do estado oculto (hidden size) de
200 (0,7237 de first-attempt AUC na validação, notebook 06, célula 24). Com o hidden size de 128,
que o app usa, a versão sem dropout foi até um pouco melhor (0,7196 contra 0,7148, numa seed só), e
a combinação do app ficou em último entre as quatro da grade, por uma diferença do tamanho do ruído.

**8. Dropout dos embeddings na avaliação.** O dropout serve ao treino, e na avaliação a prática é
desligá-lo e usar a rede inteira, o que aproxima a média das redes reduzidas amostradas no treino
(Srivastava et al., 2014). Desligado, ele também faz a mesma entrada dar sempre a mesma previsão. O
repositório tem o parâmetro `evaluating` para desligar o dropout dos embeddings
(`src/c2vRNNModel.py:36` e `53-54`), mas a avaliação nunca o passa (`src/evaluation.py:219`) nem
chama `model.eval()`, e o dropout fica ligado no teste. Ligado, cada previsão descarta 20% dos
valores ao acaso, o AUC carrega esse ruído, e o domínio do painel mudaria a cada cálculo. O dropout
de Monte Carlo mantém o dropout ligado de propósito, mas repete a previsão muitas vezes e tira a
média, o que o repositório não faz. O TCC 1 e o app desligam o dropout na avaliação
(`src/ml/code_dkt/prediction.py:32` do app), e isso fica registrado como correção de um defeito do
repositório (critério 4).

**Fora da tabela, a representação dos paths.** O repositório guarda os paths de cada solução num
texto só. Cada path vira o nó inicial, um hash do caminho e o nó final, separados por vírgula
(`src/path_extractor.py:153`), e os paths da solução são unidos por @ (`src/path_extractor.py:196`).
Na leitura, o texto é separado de volta por @ (`src/readdata.py:135`) e cada path por vírgula
(`src/readdata.py:38`). O nó inicial e o final são folhas da AST, então um literal do aluno que
contenha vírgula ou @ quebra essa leitura. O app guarda cada path como uma tupla
(`src/ml/code_dkt/ast_paths.py:121` do app) e não tem esse defeito (critério 4).

### Seção 4 do paper, dados e experimento

#### O que ficou igual

Estes pontos são iguais no repositório e no app, e também no paper quando ele trata deles. Não
pediram decisão.

- Só entram os eventos `Run.Program` (`src/preprocessing.py:11`, e
  `src/api/model_training/domain/services/training_dataset_loading.py:19` do app), que o paper chama
  de submissões, e o acerto é quando todos os testes passam (p. 54 (PDF 5)). O paper diz que 23,68%
  das tentativas estavam corretas (p. 54 (PDF 5)), e é a taxa dos `Run.Program` do CSV da CSEDM.
- Cada exercício tem o seu modelo, treinado e testado separado, "for each assignment, a new model is
  trained and tested separately" (p. 55 (PDF 6)).
- A taxa de aprendizado é 0,0005, as épocas são 40, o otimizador é o Adam e a perda é a entropia
  cruzada binária (p. 55 (PDF 6)).
- Entram as últimas 50 execuções de cada aluno (p. 55 (PDF 6)). O padding à esquerda de quem tem
  menos de 50 está na linha 20, porque o paper não trata dele.
- O treino final usa todo o conjunto de treino, sem separar validação (pp. 54–55 (PDF 5–6),
  `src/readdata.py:157`).
- O AUC é calculado com as previsões de todos os problemas juntas (`src/evaluation.py:102`, e
  `src/ml/evaluation/auc.py` do app). O paper não diz como junta os problemas e chama o AUC geral de
  "predicting all attempts (Overall)" (p. 56 (PDF 7)).

#### As decisões

A numeração continua a da seção 3.

| # | Item | Paper | Repositório | TCC 1 | App antes | App depois |
|---|---|---|---|---|---|---|
| 9 | Filtro de alunos | "410 students" (p. 54), sem dizer o filtro | nenhum | ≥ 3 execuções no dataset | ≥ 3 no exercício | nenhum |
| 10 | Ordem das execuções | as últimas 50, "the latest" (p. 55) | a do arquivo, agrupada por problema | por tempo | por tempo | por tempo |
| 11 | Primeira tentativa | a primeira em cada problema (p. 56) | o começo de cada trecho seguido do mesmo problema, na janela | a primeira dentro da janela | a primeira na sequência inteira | a primeira na sequência inteira |
| 12 | Previsão da primeira execução | a próxima tentativa, a partir do histórico (pp. 52–53) | também a primeira, a partir do padding à esquerda | não prevê | não prevê | não prevê |
| 13 | Partição | 4:1 por aluno, em cada exercício (p. 54) | 4:1 no A439, `random_state=1` | 4:1 nos 410 do dataset, depois por exercício | 4:1 por exercício no treino, a do TCC 1 no teste de regressão | 4:1 por exercício, igual ao repositório |
| 14 | Dimensão do estado oculto (hidden size) e tamanho do lote (batch size) | hidden size 200 do DKT; batch size 100 do DKT ou 1024 do code2vec | 128 e 128 | 200 e 128 | 128 e 128 | 128 e 128, com acumulação de gradiente em batches de 64 |
| 15 | Corte de gradiente | o do DKT, sem limiar | nenhum | 10 | 10 | nenhum |
| 16 | Agregação da perda | entropia cruzada, sem dizer como junta (p. 55); o DKT soma os erros de cada aluno | média de cada aluno, somada no lote | média de todas as previsões | média de todas as previsões | média de cada aluno, somada no lote |
| 17 | Determinismo na GPU | não trata | cuDNN determinístico | cuDNN determinístico | desligado | cuDNN determinístico |
| 18 | Execuções | dez, com a média (p. 55) | dez, seed 0 uma vez | dez, seeds 42 a 51 | uma, seed 42 | dez na avaliação, seeds 42 a 51, e uma no treino real, seed 42 |
| 19 | Valor de referência | Tabelas 1 e 2 (p. 55) | não tem | o paper, e mediu 73,27% em dez seeds | 73,27% ± 3pp, uma execução | teste de regressão com tolerância em torno da média de referência medida pelo app e comparação com o paper registrada |
| 20 | Preenchimento | não trata | padding à esquerda, antes das execuções | igual ao repositório | igual ao repositório | igual ao repositório |
| 21 | Vocabulário | não trata | todos os paths das soluções de treino | só os 50 amostrados, dentro da janela de 50 | só os R amostrados, antes do truncamento | todos os paths das soluções de treino |

#### Justificativas

**9. Filtro de alunos.** O paper diz que o dataset tem 410 alunos (p. 54 (PDF 5)) e não diz como
chegou a esse número. O CSV da CSEDM tem 413 alunos com `Run.Program`, e o filtro de pelo menos três
execuções do TCC 1 tira exatamente três deles, mas isso é uma reconstrução. A taxa de 23,68% não
distingue as duas leituras, porque dá 23,683% sem o filtro e 23,685% com ele. O repositório não
filtra (`src/preprocessing.py:14`), e o A439 fica com 386 alunos, contra 384 com o filtro do app
(`src/ml/code_dkt/student_split.py:17-23` do app). O app passa a não filtrar (critério 3). Para o
professor, um aluno não pode sair da análise por ter feito pouco do exercício.

**10. Ordem das execuções.** O repositório monta a sequência de cada aluno na ordem do arquivo, sem
ordenar por tempo (`src/preprocessing.py:22`). No CSV, as execuções do A439 vêm em dez blocos
contíguos, um por problema, na ordem 234, 13, 12, 232, 233, 5, 235, 236, 1 e 3, e a ordem do arquivo
difere da ordem do tempo para 369 dos 386 alunos. Com isso o modelo do repositório lê tentativas que
o aluno fez depois antes das que ele fez antes, e usa o futuro para prever o passado. O paper fica
com as últimas 50 submissões, "assuming the latest submissions were more useful" (p. 55 (PDF 6)), o
que só faz sentido na ordem do tempo. O app mantém a ordem por tempo
(`src/ml/code_dkt/student_sequences.py:12` do app, critérios 1 e 4). A Tabela 3 do paper lista os
problemas do A1 na mesma ordem dos blocos do arquivo, sem o 12 (p. 56 (PDF 7)), o que indica que os
autores tinham o arquivo nessa ordem.

**11. Primeira tentativa.** O paper avalia à parte "a student's first attempt on a task (where a
model must make predictions using only performance on other problems)" (p. 56 (PDF 7)). É a previsão
mais difícil, porque um problema pode ou não ter relação com os outros que o aluno já fez, e é a mais
útil, porque é o momento em que dá para agir antes de o aluno errar. O app marca como primeira
tentativa a primeira vez que o par aluno e problema aparece na sequência inteira, antes do
truncamento (`src/ml/code_dkt/student_sequences.py:16-19` do app), que é a definição do paper
(critério 1). O repositório marca o começo de cada trecho seguido do mesmo problema dentro da janela
(`src/evaluation.py:42`), e, com a ordem por tempo, contaria como primeira a volta a um problema
depois de tentar outro. O TCC 1 marcava a primeira dentro da janela já cortada.

**12. Previsão da primeira execução.** O paper define a tarefa como prever a próxima tentativa a
partir do histórico do aluno (pp. 52–53 (PDF 3–4)), e antes da primeira execução não há histórico.
Com o padding à esquerda, o repositório também prevê a primeira execução de quem tem menos de 50, a
partir desse padding, e conta essa previsão no AUC e no treino (`src/evaluation.py:30` e `184`). O
app só prevê depois de ver a primeira execução (`src/ml/code_dkt/prediction.py:50` do app), e fica
assim (critério 1).

**13. Partição.** O paper divide os alunos de cada exercício em treino e teste na proporção 4:1
(p. 54 (PDF 5)). O repositório faz isso no A439 com os alunos na ordem em que aparecem no arquivo e
`random_state=1` (`src/preprocessing.py:14` e `28`), o que separa 78 dos 386 alunos para o teste. O
TCC 1 dividia os 410 alunos do dataset de uma vez e depois recortava cada exercício, e o teste de
regressão do app reproduzia essa divisão. O app passa a dividir os alunos do exercício em todo lugar,
com a mesma lista, a mesma ordem e a mesma seed do repositório (critérios 1 e 3). Com as três iguais,
a divisão aleatória separa os mesmos 78 alunos de teste do código dos autores, e a comparação com o
paper deixa de ter o ruído de outra divisão aleatória. O paper não garante que as tabelas saíram
dessa divisão, mas é o código publicado com ele. A ordem depende de a importação preservar a ordem
das linhas do arquivo.

**14. Hidden size e batch size.** Pelo "defaulted as the original settings of code2vec and DKT" (p.
55 (PDF 6)), o hidden size apontaria para o do DKT, 200, já que o code2vec não tem LSTM, e o batch
size ficaria entre o 100 do DKT (Piech et al., 2015, subseção Optimization) e o 1024 do code2vec
(`config.py:49` do repositório dele). O repositório usa 128 e 128 (`src/config.py:6` e `8`), e não
se achou de onde esses valores vêm. O app mantém 128 e 128 (critério 3), e a divergência fica
registrada. Adotar os padrões originais aqui pediria, pelo mesmo raciocínio, o R de 200 do code2vec
(linha 1) e, do DKT, o dropout na saída do LSTM (linha 7) e o corte de gradiente (linha 15). O paper
do DKT não dá a taxa do dropout nem o limiar do corte. Na grade do TCC 1, trocar o hidden size de
128 por 200 mudou o first-attempt AUC da validação em menos de um ponto (notebook 06, célula 24),
abaixo do desvio de 1,34 ponto entre as seeds 42 a 51 no A439 (notebook 08, célula 16).

Com o R=100 da linha 1, o lote de 128 não cabe nos 6 GB da GPU do app, uma RTX 4050 que também
alimenta a tela. O passo de treino estourou a memória no `backward`. O app então faz acumulação de
gradiente em batches de 64 alunos, o `batch_chunk_size`, somando o gradiente deles em cada lote de
128, e só depois dá o passo do Adam, um por lote, como antes (critério 5). O gradiente esperado é o
mesmo do lote inteiro, porque o Code-DKT não tem camada que misture os alunos de um lote, como o
BatchNorm, e a perda da linha 16 soma a média de cada aluno, então a soma das perdas dos batches de
64 é a perda do lote. O resultado numérico muda, porque a soma em float depende da ordem e o dropout
amostra as máscaras a cada batch de 64. A inferência e a avaliação também vão em lotes de 64 alunos,
o `INFERENCE_CHUNK_SIZE`, e nenhum forward passa do pico do treino. Outra saída mantinha o lote
inteiro com o resultado numérico idêntico, mudando só a configuração do alocador do PyTorch, mas
deixava cerca de 800 MiB livres na GPU que o desktop também usa.

**15. Corte de gradiente.** O paper não fala de corte. O DKT corta o gradiente acima de um limiar que
não informa (Piech et al., 2015, subseção Optimization). O repositório não corta
(`src/evaluation.py:198-206`), e o limiar de 10 do TCC 1 e do app não tem fonte no paper nem no
repositório (`src/ml/code_dkt/training.py:93` do app). O app passa a não cortar (critério 3).

**16. Agregação da perda.** O paper usa a entropia cruzada binária (p. 55 (PDF 6)) e não diz como
junta os erros das previsões. O DKT, a que o paper remete, define a perda como a soma dos erros das
previsões (Piech et al., 2015, Eq. 3), e com a soma cada previsão pesa igual. O repositório tira a
média dos erros de cada aluno e soma essas médias no lote (`src/evaluation.py:171-190`), então cada
aluno pesa igual, tenha poucas ou muitas execuções. O TCC 1 e o app tiravam a média de todas as
previsões do lote (`src/ml/code_dkt/loss.py:15-26` do app), e, como no DKT, um aluno com muitas
execuções pesava mais. O app passa a seguir o repositório (critério 3), que também vale onde o
padrão do DKT difere dele. Do repositório vem só a agregação. A média de cada aluno sai dos passos
válidos do app, que começam na primeira execução real e preveem a próxima, e não inclui a previsão
da primeira execução a partir do padding à esquerda, que a linha 12 não segue. O aluno sem nenhuma
previsão válida, que no repositório não existe, fica fora da perda (critério 5). A diferença de
escala entre somar e tirar a média quase não afeta o Adam, e o que muda é o peso de cada aluno.

**17. Determinismo na GPU.** O paper não trata. O repositório liga o cuDNN determinístico e desliga a
escolha automática de algoritmo (`src/run.py:23-24`), e o TCC 1 fazia o mesmo (notebook 06, célula 3).
O app já desligava a escolha automática (`src/ml/reproducibility/random_seed.py:18` do app), mas só
ligava o cuDNN determinístico no modo estrito, usado nos testes de CPU (`random_seed.py:20-23`). O
treino na GPU roda no modo não estrito
(`src/api/model_training/infrastructure/implementations/ml_code_dkt_trainer.py:54` do app), que deixa
o cuDNN determinístico desligado (`random_seed.py:24-26`). O app passa a ligá-lo também na GPU, como o
repositório (critério 3). Com o `PYTHONHASHSEED` fixo (linha 2) e as seeds fixas, a medida das dez
execuções deve se repetir. Ligar só o cuDNN determinístico não garante resultado bit a bit na GPU, e
o modo estrito do app liga também `use_deterministic_algorithms` e `CUBLAS_WORKSPACE_CONFIG`
(`random_seed.py:20-23`). Mesmo assim, no TCC 1, com a mesma GPU e só o cuDNN determinístico, a seed
42 deu o mesmo AUC em processos diferentes nos cinco exercícios (notebook 08, célula 21). No app, as
dez seeds do A439 se repetiram bit a bit em processos diferentes, medida de 02/10/2026 no Estado.

**18. Execuções.** O paper treina e testa dez vezes e reporta a média, "to account for model
variation (e.g. due to random initialization)" (p. 55 (PDF 6)). O repositório fixa a seed 0 uma vez
e roda as dez em sequência (`src/run.py:31` e `45`), e assim nenhuma execução pode ser refeita
sozinha. Na avaliação, o app passa a rodar dez execuções com as seeds 42 a 51, como o TCC 1, uma por
execução (critério 5). As seeds mudam só a inicialização, o dropout e a ordem dos lotes, e a
amostragem aleatória dos paths fica com a `path_sampling_seed` 42 em todas, como no TCC 1, que lia
os paths de um cache único (notebook 08, célula 3). No treino real, o app continua com uma execução
e a seed 42, porque o professor recebe um modelo só, e o AUC guardado com o modelo vem dessa
execução.

**19. Valor de referência.** O TCC 1 se conferia contra o valor do paper e mediu 73,27% de
first-attempt AUC no A439, a média de dez seeds com desvio de 1,34 (notebook 08, célula 16). O teste
de regressão do app passou a usar essa média como referência, comparando uma execução com a
tolerância de ± 3pp, e o app media 0,7608, a 0,19 ponto do limite superior da tolerância. Ele passa
a ter dois papéis separados.
- O teste de regressão roda as dez execuções no A439 e confere a média com uma tolerância em torno
  da média de referência que o app medir depois da implementação. Ele serve para detectar que o
  código mudou de comportamento.
- A comparação com o paper vira um resultado registrado aqui, sem ser um teste que falha. Ela
  compara a média das dez execuções com a Tabela 1, o AUC geral dos cinco exercícios (74,31, 76,56,
  80,40, 72,75 e 79,14%), e a média e o desvio com a Tabela 2, que no A1 dá 75,74% com desvio de
  0,69 na primeira tentativa e 74,31% com desvio de 0,90 no geral (p. 55 (PDF 6)).

As correções decididas, como a ordem por tempo, podem afastar o número do app do número do paper de
forma legítima, e um teste que exigisse o número do paper empurraria o código de volta para os
defeitos do repositório.

A tolerância do teste de regressão é de ±0,1 ponto em torno de 0,7278, a média de referência das dez
seeds da primeira tentativa no A439 medida em 02/10/2026, decisão do autor do trabalho tomada no
mesmo dia (critério 5). As dez seeds se repetem bit a bit nesta máquina (linha 17), então qualquer
mudança na média quer dizer que o código, as dependências ou o ambiente mudaram. Uma tolerância de
dois erros padrão da média (±0,5 ponto) deixaria passar uma mudança de comportamento menor que meio
ponto. Uma troca de driver, de GPU ou de dependência que faça o teste de regressão falhar pede uma
nova medida da média de referência, registrada aqui.

A comparação com o paper, medida em 02/10/2026 com as dez seeds em cada exercício, em porcentagem e
com o desvio amostral. O A1 é o 439, pela Tabela 3 do paper e pelo repositório, e o A2 a A5 são o
487, o 492, o 494 e o 502, inferidos da ordem crescente dos ids no TCC 1, porque o paper não diz.
O AUC de cada seed está em `docs/results/code_dkt_literature_comparison.json`.

| Exercício | App, primeira tentativa | App, geral | Paper, geral (Tabela 1) |
|---|---|---|---|
| A1 (439) | 72,78 ± 0,81 | 69,25 ± 0,86 | 74,31 |
| A2 (487) | 77,97 ± 0,70 | 75,17 ± 0,76 | 76,56 |
| A3 (492) | 86,09 ± 0,59 | 77,82 ± 0,37 | 80,40 |
| A4 (494) | 78,48 ± 1,06 | 73,27 ± 0,74 | 72,75 |
| A5 (502) | 83,86 ± 0,67 | 77,28 ± 0,52 | 79,14 |

No AUC geral, o app fica abaixo da Tabela 1 em quatro exercícios, de 1,39 a 5,06 pontos, e 0,52
acima no A4. No A1, a Tabela 2 dá 75,74 ± 0,69 na primeira tentativa, 2,96 pontos acima do app, e
74,31 ± 0,90 no geral (p. 55 (PDF 6)). O paper só reporta a primeira tentativa e o desvio no A1, e
não diz se o desvio é amostral. O efeito de cada decisão em que o app difere do repositório não foi
medido separado.

O AUC da primeira tentativa no A439 com a seed 42, a cada grupo de decisões, foi de 0,7595 com o
`PYTHONHASHSEED=0` e a partição do TCC 1 (linha 2), 0,7221 com a partição do repositório (linhas 9 e
13), 0,7271 com os paths, o vocabulário e o token desconhecido (linhas 1, 3 e 21, com a acumulação
de gradiente em batches de 64 da linha 14) e 0,7228 com a rede e o treino (linhas 6, 7, 15, 16 e
17). A troca da partição mudou o conjunto de teste, e uma seed só não separa o efeito de cada grupo
do ruído entre seeds, de 0,81 ponto no A439.

**20. Preenchimento.** O paper não trata de como os lotes são montados e diz só que o estado do RNN
começa no vetor zero (p. 53 (PDF 4)). O repositório, o TCC 1 e o app põem o padding à esquerda,
antes das execuções (`src/readdata.py:122` e `127`, e `src/ml/code_dkt/model_input.py:51` do app), e
o app mantém (critério 3). Fica registrada uma limitação possível, não medida. O estado começa
zerado na primeira posição de padding e atravessa todas elas antes da primeira execução, e o número
de posições de padding depende de quantas execuções o aluno fez no total. Assim, o estado inicial de
quem tem menos de 50 execuções pode carregar o tamanho da história inteira, uma informação que só
existe no fim.

**21. Vocabulário.** O vocabulário de nós e paths sai só dos alunos de treino, nos três, e é contado
antes do corte nas últimas 50 execuções no repositório e no app (`src/readdata.py:68-91`, e
`src/ml/code_dkt/train_and_evaluate.py:70-86` do app). O que entra na contagem não é igual. O
repositório conta todos os paths de cada solução de treino, antes de ficar com os 100 primeiros
(`src/readdata.py:140`), e o app conta só os R paths amostrados
(`src/ml/code_dkt/ast_paths.py:126-128` do app). No app, um path do treino que não foi amostrado
vira token desconhecido (UNK). No repositório ele ganha um índice, e, se nunca for uma das entradas
do treino, o embedding dele fica com o valor aleatório da inicialização. O TCC 1 contava só os 50
paths amostrados, dentro da janela de 50 (notebook 06, células 11 e 14). O app passa a contar todos
os paths das soluções de treino, como o repositório (critério 3). O paper não trata do vocabulário,
e o embedding não treinado de um path que nunca foi entrada não é um defeito pelos termos do
critério 4, porque não deixa o futuro entrar na previsão nem o acaso na avaliação. A amostragem
aleatória de 100 paths da linha 1 tende a deixar menos paths com embedding não treinado do que os
100 primeiros, porque não fica sempre com o começo do método. Para contar todos, o cache passa a
guardar todos os paths de cada solução, e a amostragem aleatória acontece na montagem da entrada.

#### Fora do escopo

- **A busca de hiperparâmetros.** O paper escolheu os valores repetindo a busca 100 vezes sobre uma
  parte do treino (p. 55 (PDF 6)). O app usa os valores que o paper escolheu e não refaz a busca, nem
  para os dados de cada turma. É uma premissa do app que esses valores, ajustados na CSEDM, servem
  para outras turmas.
- **Os baselines.** O paper compara o Code-DKT com o DKT, o BKT, o DKT-TFIDF e o DKT-Expert (§4.3).
  O TCC 1 comparou o Code-DKT só com o BKT e o DKT e acrescentou um srcML-DKT, que não está no paper
  (notebook 07). O DKT-TFIDF e o DKT-Expert não foram reproduzidos, e o app usa só o Code-DKT.

### O que o app acrescenta ao Code-DKT

O paper usa o modelo para prever a próxima tentativa e avalia essa previsão. O app usa a mesma rede
para mostrar ao professor o domínio de cada aluno, e isso não está no paper.

- **O domínio de cada problema.** O app lê o vetor de saída do último passo de cada aluno, com a
  probabilidade de acerto em cada problema do exercício, inclusive os que ele não tentou, como Piech
  et al. (2015) leem a saída do DKT (`predict_current_state`, em `src/ml/code_dkt/prediction.py:65`
  do app). A previsão usada no AUC continua sendo uma função separada (`predict_code_dkt`, na linha
  14 do mesmo arquivo).
- **O domínio de cada conceito.** É a média do domínio dos problemas que exigem o conceito, pela
  Q-matrix do exercício. O Code-DKT trata cada problema como um KC ("We use problemIDs for KCs in this
  work", p. 52 (PDF 3)), e os conceitos do app vêm do KCGen-KT, validados pelo professor. Os
  conceitos não entram no treino, e a rede continua sendo a do Code-DKT.
- **O treino na turma do professor.** O app treina um modelo por exercício sobre os dados que o
  professor importou, e não sobre um conjunto fixo, com os mesmos hiperparâmetros para toda turma, os
  das seções 3 e 4 acima. O Estado diz quais decisões já estão no código.

### Estado

| # | Estado |
|---|---|
| 1 | Decidida em 30/09/2026, implementada em 01/10/2026 no commit `fb90a7f`. O TCC 1 mediu 2,2 GB de VRAM com R=50. Com R=100, o lote de 128 inteiro não coube na GPU. A alocação falhou com 5.289 de 6.141 MiB em uso no `nvidia-smi`, contando a tela, por fragmentação, e sem ela o lote ocupou 5.345 MiB. Com acumulação de gradiente em batches de 64 (linha 14), o treino do A439 teve pico de 3.187 MiB |
| 2 | Decidida em 30/09/2026, implementada em 01/10/2026 no commit `68b3cea`. Com `PYTHONHASHSEED=0`, o teste de regressão como estava antes da implementação, no commit `eb95fa0`, na partição do TCC 1 com 410 alunos, uma seed, `strict=False` e na GPU, deu 0,7595 |
| 3 | Decidida em 30/09/2026, implementada em 01/10/2026 no commit `fb90a7f` |
| 4 | Decidida em 30/09/2026, sem mudança no código |
| 5 | Decidida em 30/09/2026, sem mudança no código |
| 6 | Decidida em 30/09/2026, implementada em 01/10/2026 no commit `277403c` |
| 7 | Decidida em 30/09/2026, implementada em 01/10/2026 no commit `277403c` |
| 8 | Decidida em 30/09/2026, sem mudança no código |
| 9 | Decidida em 30/09/2026, implementada em 01/10/2026 no commit `4cf7131`. No A439 entram os 386 alunos com `Run.Program` |
| 10 | Decidida em 30/09/2026, sem mudança no código |
| 11 | Decidida em 01/10/2026, sem mudança no código |
| 12 | Decidida em 01/10/2026, sem mudança no código |
| 13 | Decidida em 01/10/2026, implementada em 01/10/2026 no commit `4cf7131`. A importação preserva a ordem do arquivo, conferida por teste, e no A439 o app separa os mesmos 78 alunos de teste do procedimento do repositório |
| 14 | Decidida em 01/10/2026, sem mudança na dimensão do estado oculto (hidden size) nem no tamanho do lote (batch size). A acumulação de gradiente em batches de 64, decisão do app pelo critério 5, foi implementada em 01/10/2026 no commit `fb90a7f` |
| 15 | Decidida em 01/10/2026, implementada em 01/10/2026 no commit `277403c` |
| 16 | Decidida em 01/10/2026, implementada em 01/10/2026 no commit `277403c` |
| 17 | Decidida em 30/09/2026, implementada em 01/10/2026 no commit `277403c`. Em 02/10/2026, no commit `c7dfa3a`, as dez seeds do A439 deram os mesmos valores de primeira tentativa e geral, bit a bit, em quatro processos diferentes |
| 18 | Decidida em 30/09/2026, implementada em 02/10/2026 no commit `c7dfa3a`, no `evaluate_over_seeds`, que o teste de regressão e a comparação com o paper usam |
| 19 | Decidida em 30/09/2026, implementada em 02/10/2026 no commit `c7dfa3a`. A tolerância do teste de regressão é de ±0,1 ponto em torno da média de referência, 0,7278, e a comparação com o paper está na justificativa 19 |
| 20 | Decidida em 01/10/2026, sem mudança no código |
| 21 | Decidida em 01/10/2026, implementada em 01/10/2026 no commit `fb90a7f`. O vocabulário do A439 tem 553 nós e 38.179 paths, e 4,1% dos paths do teste ficam fora do vocabulário, contra 6,0% no TCC 1 |

## KCGen-KT

A discutir, depois do Code-DKT.

### Fontes

- **Paper.** Duan et al. (2025), na versão 2502.18632v3 do arXiv, que o TCC 1 usou. O artigo saiu
  depois nos Findings of ACL 2026 (Duan et al., 2026), com o título "Automated Knowledge Component
  Generation and Interpretable Knowledge Tracing in Coding Problems".
- **Repositório oficial.** [umass-ml4ed/kcgen-kt](https://github.com/umass-ml4ed/kcgen-kt).
- **TCC 1.** O notebook `notebooks/03b_kc_generation.ipynb`.

## Referências

ALON, U.; ZILBERSTEIN, M.; LEVY, O.; YAHAV, E. code2vec: learning distributed representations of
code. Proceedings of the ACM on Programming Languages, v. 3, n. POPL, 2019.

DUAN, Z. et al. Automated Knowledge Component Generation for Interpretable Knowledge Tracing in
Coding Problems. arXiv:2502.18632v3, 2025.

DUAN, Z. et al. Automated Knowledge Component Generation and Interpretable Knowledge Tracing in
Coding Problems. In: Findings of the Association for Computational Linguistics: ACL 2026. 2026.
p. 33405–33423. Disponível em: https://aclanthology.org/2026.findings-acl.1670/.

PIECH, C. et al. Deep Knowledge Tracing. In: Advances in Neural Information Processing Systems 28
(NIPS 2015). 2015.

SHI, Y.; CHI, M.; BARNES, T.; PRICE, T. Code-DKT: A Code-based Knowledge Tracing Model for
Programming Tasks. In: Proceedings of the 15th International Conference on Educational Data Mining
(EDM 2022). Durham: International Educational Data Mining Society, 2022. p. 50–61. DOI
10.5281/zenodo.6853105.

SRIVASTAVA, N. et al. Dropout: a simple way to prevent neural networks from overfitting. Journal of
Machine Learning Research, v. 15, p. 1929–1958, 2014.
