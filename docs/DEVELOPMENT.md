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

### Fontes

- **Paper.** Duan et al. (2026), nos Findings of ACL 2026, pp. 33405 a 33423. As páginas citadas
  são as dos anais, com a do PDF entre parênteses. A página do PDF é a dos anais menos 33404. O TCC 1
  usou a versão 2502.18632v3 do arXiv (Duan et al., 2025), que tem o mesmo método e os mesmos
  prompts da geração de KCs. O ACL renumera as tabelas (a Tabela 5 da v3 é a 6 do ACL, e as Tabelas
  7 a 10 da v3 são as 8 a 11), acrescenta as seções Limitations e Ethical Considerations e diz no
  Apêndice C que o HAC usa o scipy. A v3 só é citada quando o assunto é o TCC 1 ou a diferença entre
  as duas versões.
- **Repositório oficial.** [umass-ml4ed/kcgen-kt](https://github.com/umass-ml4ed/kcgen-kt), commit
  `f75da27`. A geração de KCs está em `KC_gen.py`, e os arquivos e as linhas citados são desse
  commit. O repositório não roda sozinho. Faltam os vetores das soluções, que o `KC_gen.py` lê
  prontos da pasta `code_embedding/`, e o dado, `data/dataset_time.pkl`, que vem de um Google Drive.
  O trecho que calculava os vetores está comentado (`KC_gen.py:431-457`).
- **Planilha oficial da CSEDM.** Os enunciados e as 18 tags de conceito dos 50 problemas da
  CodeWorkout não vêm no ProgSnap2. Estão numa
  [planilha](https://docs.google.com/spreadsheets/d/1-APxPAVP3PylM0fskzDNgpalj1DTuMqDLkgBC5QxJdg/edit#gid=0)
  que os organizadores do Second CSEDM Data Challenge ligam na página do dataset, "The prompts for
  each problem can be found in this spreadsheet". O link saiu da cópia da página no Wayback Machine,
  de 31/03/2024. A mesma página diz que as tags "are just one researcher's judgement and should not
  be taken as ground truth". O `data/prompt_concept.csv` do repositório tem o mesmo conteúdo da
  planilha, casado por `AssignmentID` e `ProblemID` e conferido em 03/10/2026, com uma coluna a mais,
  `Test Case Status`, e as linhas em outra ordem.
- **App.** As linhas do app citadas, marcadas como "do app", são do commit `855d69d`, de antes da
  implementação.
- **TCC 1.** [scuiki/tcc.edm.kt](https://github.com/scuiki/tcc.edm.kt), commit `0e8807c`, com o
  notebook `notebooks/03b_kc_generation.ipynb`, de onde o código do app foi portado, e a nota
  `docs/refs/duan2025_automatedkc.md` sobre o paper. As células são contadas pela posição no
  arquivo, a partir do 0 e incluindo as de texto.
- **O nome.** No paper, KCGen-KT nomeia o método de KT (§2.2) e às vezes o conjunto, como na legenda
  da Tabela 1 (p. 33406 (PDF 2)) e na conclusão (p. 33413 (PDF 9)). O pipeline de geração de KCs
  (§2.1) não tem nome próprio. O repositório também se chama `kcgen-kt`. No app, KCGen-KT designa só
  a geração de KCs, e quem usa os KCs é o Code-DKT.

### Critério

Quando as fontes discordam, a decisão segue esta ordem. É o critério do Code-DKT sem o item das
equações, que a geração de KCs não tem, e com dois acréscimos, o código comentado e a divergência
obrigada.

1. O que o paper especifica vale o paper, mesmo onde o repositório faz diferente.
2. O que o paper não especifica vale o repositório oficial. O código comentado do repositório não
   roda, e não se sabe se é o que gerou os resultados do paper. Ele vale como indício, e a decisão
   fica registrada como do app, com o apoio dele.
3. Onde o repositório tem um defeito, como sortear sem semente, vale a prática estabelecida, e a
   correção fica registrada.
4. Onde o método dos autores, no paper ou no repositório, pede algo que o dado de uma turma ou o
   ambiente do app não oferece, vale a adaptação mais próxima, sem etapa nova, registrada como
   divergência obrigada. São os casos do enunciado do problema, das tags de KC escritas por humanos,
   do desempenho do modelo de KT para escolher o número de grupos, do GPT-4o e da temperatura 0 do
   repositório.
5. O que nenhum dos dois define é decisão do app, registrada aqui.

A coluna Origem das tabelas diz de onde vem cada escolha do app. "Duan (paper)" e "Duan
(repositório)" são o método dos autores. "App" é adequação do app, com o critério que a justifica.

### Seção 2.1 do paper, a geração de KCs

O §2.1 gera os KCs de um problema em três passos, "1) generating KCs associated with each problem
and their descriptions separately through few-shot prompting, 2) clustering KCs across all
problems, and 3) summarizing each cluster to obtain a finalized description of each KC" (p. 33406
(PDF 2)). A Q-matrix sai de trocar cada KC de um problema pelo nome do seu grupo (p. 33407 (PDF 3)).
Antes do primeiro passo, o pipeline escolhe as soluções corretas que o LLM vai ler.

#### O que ficou igual

Estes pontos são iguais no paper, no repositório e no app, e não pediram decisão.

- Só soluções corretas entram, com Score igual a 1,0. O paper diz "we include correct student
  submissions as examples" (p. 33407 (PDF 3)), e na ablação incluir soluções incorretas derruba o AUC
  de 0,812 para 0,773 (Tabela 4, p. 33411 (PDF 7)). O repositório filtra `Score_x == 1.0`
  (`KC_gen.py:570`) e roda com `n_incor=0` (`KC_gen.py:646`), e o app filtra `is_correct == 1`
  (`kcgen_kt_generator.py:75` do app).
- O código vai ao LLM como texto. O repositório monta o prompt com o texto das soluções
  (`KC_gen.py:103`), embora o README fale em AST, e o app faz o mesmo
  (`candidate_generation.py:141-143` do app). Na ablação, trocar o código pela AST derruba o AUC de
  0,812 para 0,784 (Tabela 4, p. 33411 (PDF 7)).
- O LLM é chamado uma vez por problema, com as soluções daquele problema (p. 33407 (PDF 3);
  `KC_gen.py:264`). O app herda a limitação que o paper reconhece, a de às vezes perder KCs comuns a
  vários problemas por gerar cada um em separado (p. 33413 (PDF 9)).
- A geração usa os dados de todos os alunos, sem separar treino e teste. O paper fala em "all
  correct student submissions" (p. 33407 (PDF 3)), e o repositório lê o dado inteiro
  (`KC_gen.py:644`). O TCC 1 usava só o treino (notebook 03b, célula 4). Os KCs não entram no treino
  do Code-DKT, então o first-attempt AUC do app não é afetado.

#### A amostragem das soluções

| # | Item | Paper | Repositório | TCC 1 | App antes | App depois | Origem |
|---|---|---|---|---|---|---|---|
| 1 | Como escolhe as soluções | agrupa os vetores das soluções corretas e sorteia uma por grupo (p. 33407) | igual ao paper, no `main()` | uma por faixa de tentativas até acertar | as faixas do TCC 1, com uma solução por problema na prática | igual ao paper | Duan (paper) |
| 2 | Modelo dos vetores das soluções | CodeBERT (p. 33407) | `graphcodebert-base`, só no código comentado | não tem | não tem | `microsoft/codebert-base` | Duan (paper) |
| 3 | Vetor de cada solução | não trata | média dos vetores da última camada pela máscara de atenção, norma L2 e corte em 512 tokens, em código comentado | não tem | não tem | igual ao código comentado | app, critério 2 |
| 4 | Algoritmo do agrupamento | "a clustering algorithm" (p. 33407) | HAC, distância cosseno, ligação média | não tem | não tem | igual ao repositório | Duan (repositório) |
| 5 | Quantas soluções por problema | 5 no experimento principal (p. 33410) | 5 | 5 | 5 declaradas, 1 na prática | 5 | Duan (paper) |
| 6 | De onde se sorteia | todas as submissões corretas (p. 33407) | todas as corretas, com repetições do mesmo aluno | a primeira correta de cada aluno | a primeira correta de cada aluno | todas as execuções corretas do problema | Duan (paper) |
| 7 | Sorteio dentro do grupo | uma por grupo, sem semente | `random.sample` sem semente | um `Random(42)` para todos os problemas | um `Random(42)` por problema | um `Random(42)` por problema | app, critério 3 |
| 8 | Menos de 5 soluções distintas | não trata | não trata | uma por faixa não vazia, até 5 | uma, porque todas caem na primeira faixa | tantos grupos quanto o menor entre 5 e o número de soluções distintas | app, critério 5 |

**1. Como escolhe as soluções.** O paper diz "we apply a clustering algorithm to the CodeBERT (Feng
et al., 2020) embeddings of all correct student submissions and sample one per cluster, with the
number of clusters controlling the diversity of examples" (p. 33407 (PDF 3)), porque um problema
pode ser resolvido de vários jeitos válidos, cada um com os seus KCs. O `main()` do repositório usa
esse caminho (`random_draw=False`, `KC_gen.py:646`). O padrão da função é um sorteio simples com
`random_state=42` (`KC_gen.py:489`), que o repositório usa quando o número de soluções é 1
(`KC_gen.py:574-575`). O TCC 1 dividia as soluções corretas pelo número de tentativas até acertar
(1, 2 a 3, 4 a 6, 7 a 10 e mais de 10) e sorteava uma por faixa (notebook 03b, célula 4). O app
(`solution_sampling.py:13` do app) e o notebook (células 0 e 4) atribuem as faixas ao Duan, embora a
célula 3 do notebook as chame de heurística do próprio TCC 1. Elas não estão no paper nem no
repositório. O número de tentativas mede o esforço do aluno, e o paper quer cobrir estratégias de
solução diferentes. O exemplo do Apêndice B do ACL, o problema bobThere (A492, problema 128), tem
duas soluções corretas, uma com laço e outra com expressão regular, "Although both code submissions
are correct, they rely on different valid strategies leveraging different KCs" (p. 33417 (PDF 13)).
Na variante CodeWorkout da CSEDM, 5 das 359 execuções corretas desse problema, de dois alunos, usam
expressão regular (`matches` em quatro e `replaceAll` em uma), e nenhum dos seis KCs que o TCC 1
gerou para ele trata disso (`results/kc_raw_A492.json`
do TCC 1). Além disso, o app contava as tentativas só sobre as execuções corretas
(`kcgen_kt_generator.py:75` e `86` do app), então todo aluno caía na primeira faixa e o LLM lia uma
solução por problema, a configuração de menor AUC da Tabela 6 (0,804, contra 0,815 com cinco,
p. 33418 (PDF 14)). O método do paper não conta tentativas, e o problema some com ele. Pelo critério
1, o app segue o paper.

**2. Modelo dos vetores das soluções.** O paper cita o CodeBERT (Feng et al., 2020) (p. 33407
(PDF 3)). O repositório passa o nome `microsoft/graphcodebert-base` para a função de agrupamento
(`KC_gen.py:502`), mas ela só usa o nome no trecho comentado e lê os vetores de arquivos `.npy` que
não estão no repositório (`KC_gen.py:459-461`). O GraphCodeBERT (Guo et al., 2021) é um modelo
posterior da mesma família, treinado também com o fluxo de dados entre as variáveis. Não há como
saber qual dos dois gerou os arquivos. Pelo critério 1, o app usa o CodeBERT, no checkpoint
`microsoft/codebert-base`.

**3. Vetor de cada solução.** O CodeBERT devolve um vetor por token, e o paper não diz como juntar os
vetores de uma solução num só. O trecho comentado do repositório (`KC_gen.py:431-457`) corta o código
no limite do tokenizador, de 512 tokens, tira a média dos vetores da última camada pesada pela
máscara de atenção, que ignora o padding, e normaliza o resultado para norma 1. A alternativa com o
vetor do primeiro token também está comentada (`KC_gen.py:444-445`). Pelo critério 2, o app faz como
o trecho comentado, e a escolha fica registrada como do app. Uma solução maior que 512 tokens tem o
fim cortado.

**4. Algoritmo do agrupamento.** O paper diz só "a clustering algorithm" (p. 33407 (PDF 3)). O
repositório usa o `AgglomerativeClustering` do scikit-learn com distância cosseno e ligação média,
com tantos grupos quanto as soluções a sortear (`KC_gen.py:463-467`). Pelo critério 2, o app segue o
repositório. É o mesmo tipo de agrupamento que o paper usa para os KCs no segundo passo (p. 33407
(PDF 3)), aqui sobre os vetores das soluções.

**5. Quantas soluções por problema.** O experimento principal usa "5 student submissions per
problem" (p. 33410 (PDF 6)), e o repositório roda com `n_correct=5` (`KC_gen.py:646`). A Tabela 6
(p. 33418 (PDF 14)) testa 1, 2, 5, 7 e 10 soluções, com AUC de 0,804, 0,812, 0,815, 0,812 e 0,816, e o
texto conclui que "the performance increases and saturates after more than five submissions". Essa
ablação foi feita no nível de abstração mais fino. O TCC 1 cita uma Tabela 5 com 1, 3, 5, 7 e 10
soluções e AUC de 0,798, 0,807, 0,812, 0,811 e 0,810, e chama o 5 de ponto ótimo (notebook 03b,
células 3 e 4, e `docs/refs/duan2025_automatedkc.md` do TCC 1). Esses valores não estão em nenhuma
das duas versões do paper, e o 5 é o valor da configuração principal, não um ótimo medido.

**6. De onde se sorteia.** O paper sorteia entre "all correct student submissions" (p. 33407
(PDF 3)). O repositório filtra as corretas do dado inteiro, sem tirar as repetições do mesmo aluno no
mesmo problema (`KC_gen.py:570`), e só reduz o dado à primeira submissão na carga do modelo de KT
(`data_loader.py:95-96`). A restrição à primeira correta de cada aluno, no TCC 1
(`load_correct_samples`, notebook 03b, célula 4) e no app (`solution_sampling.py:25-26` do app),
servia para contar as tentativas das faixas e perde a razão de ser com o método do paper. A frase "we
analyze students' first submissions to each problem" (p. 33409 (PDF 5)) trata do dado do modelo de
KT, e não da geração de KCs. Pelo critério 1, entram todas as execuções corretas do problema. Um
aluno que mandou a mesma solução correta mais de uma vez aparece mais de uma vez, como no
repositório.

**7. Sorteio dentro do grupo.** O paper diz "sample one per cluster" (p. 33407 (PDF 3)), sem
semente. O repositório usa `random.sample` do módulo `random` sem semente (`KC_gen.py:480`), e o
sorteio muda a cada execução, um defeito de reprodutibilidade (critério 3). O app mantém o que já
faz, um `Random(42)` novo para cada problema (`solution_sampling.py:50` do app), e o sorteio de um
problema não depende dos outros nem da ordem em que são processados. O TCC 1 usava um `Random(42)`
só para todos os problemas (notebook 03b, célula 4), e o sorteio de um problema dependia dos
anteriores. A semente 42 é a do resto do app.

**8. Menos de 5 soluções distintas.** O agrupamento precisa de pelo menos tantas soluções quanto
grupos e, com códigos idênticos, pode pôr cópias da mesma solução em grupos diferentes e mandar a
mesma solução duas vezes ao LLM. O paper e o repositório não tratam do caso. O app usa tantos grupos
quanto o menor entre 5 e o número de soluções de texto distinto. Com uma solução correta só, o LLM lê
essa (critério 5).

#### O prompt de geração

| # | Item | Paper | Repositório | TCC 1 | App antes | App depois | Origem |
|---|---|---|---|---|---|---|---|
| 9 | LLM | GPT-4o (p. 33406) | `gpt-4o` | `claude-haiku-4-5-20251001` | `claude-haiku-4-5-20251001` | `claude-sonnet-5-5`, na geração e na nomeação | app, critério 4 |
| 10 | Temperatura | não trata | 0 | a padrão | a padrão | a padrão | app, critério 4 |
| 11 | Descrição do problema na resposta | não tem | não tem | o LLM deduz uma descrição do problema pelo código e a devolve | igual ao TCC 1, mostrada na lista de problemas e prevista na origem do conceito | não tem | Duan (paper) |
| 12 | Texto do prompt | Tabela 9 (p. 33421) | o mesmo texto de sistema da Tabela 9 | próprio | igual ao TCC 1 | o do Duan, mudado só onde o dado da turma obriga | Duan (paper) |
| 13 | Texto-base | Tabela 9, um exemplo de prompt com 1 exemplo in-context e 1 solução | o mesmo texto de sistema, abertura e fecho, com outros rótulos, JSON válido e a forma para n soluções e 2 exemplos | não usa | não usa | o do repositório | Duan (repositório) |
| 14 | Enunciado do problema | entra no prompt | entra, vindo da planilha oficial | não entra | não entra | entra quando o exercício tem enunciado, e sem ele só as duas linhas do enunciado saem | Duan (paper), e app, critério 4, sem enunciado |
| 15 | Exemplos in-context | "a few", feitos das tags humanas do dataset, e 1 na Tabela 9 | 2 fixos, o dos sinais de mais (A492, problema 32) e o da multa por velocidade (A439, problema 13) | 2 próprios, com código | iguais aos do TCC 1 | iguais aos do repositório | Duan (repositório) |
| 16 | Ordem dos campos e limites da resposta | a justificativa antes do nome e em exatamente 1 frase, sem limite de KCs nem de palavras do nome | igual ao paper | o nome antes da justificativa, 3 a 7 KCs e 3 a 8 palavras | igual ao TCC 1 | igual ao repositório | Duan (repositório) |
| 17 | Validação da resposta | não trata | modo JSON da OpenAI, guarda só o nome | confere as chaves da resposta e o nome e a justificativa de cada KC, sem nova tentativa | schema da CLI, nova tentativa só em erro transitório | valida a estrutura e tenta de novo se vier inválida | app, critério 5 |

**9. LLM.** O paper usa o GPT-4o, "an advanced proprietary LLM with strong reasoning and programming
abilities" (p. 33406 (PDF 2)), na geração e na nomeação dos grupos, e o repositório também
(`KC_gen.py:100` e `646`). O app chama o Claude pela CLI `claude`, na assinatura, e não chama a API
da OpenAI, então o GPT-4o não é possível (critério 4). A adaptação mais próxima é um modelo forte da
família, o Claude Sonnet 5.5 (`claude-sonnet-5-5`), e não o Claude Haiku 4.5 do TCC 1, escolhido
"por razões de custo" (`docs/METODOLOGIA_FERRAMENTAS.md:401` do TCC 1). O Sonnet 5.5 não tem versão
datada como a do Haiku 4.5, então a extração grava o ID do modelo e a versão do prompt, e a data já
fica no job. Nenhuma das duas versões do paper compara LLMs na geração de KCs, então os números do
paper valem para o GPT-4o, e a equivalência com qualquer outro modelo não foi testada. A mesma linha
da metodologia do TCC 1 diz que o paper documenta robustez à troca de LLM, o que não está no paper.

**10. Temperatura.** O repositório usa temperatura 0 (`KC_gen.py:646`). O Sonnet 5.5 recusa
temperatura diferente da padrão, e a CLI não tem opção para ela, então o app usa a padrão
(critério 4). Temperatura 0 também não garantia respostas idênticas. O que torna a extração
repetível no app é o cache das respostas do LLM, com chave no modelo, na versão do prompt, no texto
de sistema, no schema e no prompt (`llm_response_cache.py:23-40` do app). Uma extração nova com o
cache vazio pode dar outros KCs.

**11. Descrição do problema na resposta.** No paper, o enunciado do problema é entrada do prompt
(Tabela 9, p. 33421 (PDF 17)), e o LLM devolve só os KCs. O TCC 1, sem enunciado, pedia ao LLM uma
descrição de uma a duas frases deduzida das soluções e a recebia na resposta (notebook 03b, célula
8). O app a grava e a mostra na lista de problemas da tela Conceitos, e o desenho da origem do
conceito, ainda não implementado, também a prevê (`docs/DESIGN.md:208-210`). É uma etapa que o paper
não tem, e a adaptação do critério 4 não cria etapa nova. A descrição sai da resposta, da tela e do
desenho.

**12. Texto do prompt.** O paper mostra o prompt da geração na Tabela 9 (Apêndice G.1, p. 33421
(PDF 17)), e o repositório executa o mesmo texto de sistema (`KC_gen.py:100-170`). O TCC 1 escreveu
um prompt próprio (notebook 03b, célula 8), com outro papel para o modelo, limites de 3 a 7 KCs por
problema e de 3 a 8 palavras por nome, sem a definição de KC e com exemplos próprios, e o app o
copiou (`candidate_generation.py:35-158` do app). O notebook e o app atribuem esses exemplos à
Tabela 8 da v3, que tem um exemplo só, de outro problema e sem código. Pelo critério 1, o app copia o
prompt do Duan e o muda só onde o dado da turma obriga (critério 4).

**13. Texto-base.** O §2.1 diz "See Appendix G for the exact prompt used for all steps in our KC
generation pipeline" (p. 33407 (PDF 3)), mas a legenda da Tabela 9 diz "Example prompt for KC
generation with one in-context example and one student solution" (p. 33421 (PDF 17)). A tabela
mostra um caso com um exemplo e uma solução, e o modelo de JSON dela não tem as chaves de cada KC. O
`KC_gen.py:100-170` tem as mesmas palavras no texto de sistema, na abertura e no fecho da mensagem do
usuário. Os rótulos são outros. A tabela usa "Example 1:", "Problem:", "Expected Output: KC 1: ..." e
"First sample solution is:", e o repositório usa `# Example 1:`, `## Problem:`, `## Expected KCs:`
com os KCs num JSON, `# Problem:` e `## Sample solution 1:` (`KC_gen.py:103` e `110-119`), com o JSON
válido e a forma para n soluções e dois exemplos. O app segue o repositório também nos rótulos,
porque a tabela é uma ilustração com uma solução e o repositório é o texto que os autores executaram,
e essa leitura do critério 2 fica registrada. O app copia o texto do repositório e só troca
`{language}` por Java e `{len(code_ls)}` pelo número de soluções.

**14. Enunciado do problema.** O paper põe o enunciado no prompt (Tabela 9, p. 33421 (PDF 17)) e diz
que a CodeWorkout traz "problem textual statements and human-written KC tags" (p. 33409 (PDF 5)). Os
enunciados não vêm no ProgSnap2, mas na planilha oficial do desafio (Fontes). O TCC 1 dizia que a
CSEDM não traz enunciados (notebook 03b, célula 7) e pedia ao LLM uma descrição deduzida do código
(linha 11). O app passa a aceitar exercícios com e sem enunciado. A importação acha sozinha o
arquivo de enunciados entre os arquivos enviados. A `MainTable.csv` e o `CodeStates.csv` ela já acha
pelo nome, e o arquivo de enunciados ela acha pelo cabeçalho da planilha oficial (`AssignmentID`,
`ProblemID` e `Requirement`), porque o nome dele não é padrão. Com enunciado, o prompt é o do
repositório sem mudança (critério 1). Sem enunciado, só as duas linhas do enunciado do problema
saem, `# Problem:` e o texto, e o resto fica igual, inclusive os exemplos com os enunciados deles
(critério 4). A CSEDM de referência é extraída com os enunciados da planilha.

**15. Exemplos in-context.** O paper diz que os exemplos vêm das tags humanas de cada dataset,
"prompting GPT-4o to convert human-written topic tags, such as “If-else”, from each dataset into
more fine-granular natural language descriptions" (p. 33407 (PDF 3)), e a Tabela 9 mostra um, o
problema dos sinais de mais. O repositório usa dois fixos, esse e o da multa por velocidade
(`KC_gen.py:250-260`), com o enunciado e as tags da planilha oficial, convertidas para linguagem
natural por uma lista fixa (`KC_gen.py:544-547`) e não por uma chamada ao LLM. As tags são o
julgamento de um pesquisador, como diz a página do dataset, mas são escritas por humano, como o ACL
exige, "requiring at least one human-written example to produce low-level KCs" (p. 33414 (PDF 10)).
Os exemplos do TCC 1, sumArray e letterGrade, não vêm do paper nem do repositório e saem. O app usa
os dois do repositório, iguais, em toda turma (critério 2). Na CSEDM, o problema 13 do A439 e o 32 do
A492 são extraídos com os próprios KCs humanos no prompt, porque o repositório não os pula
(`KC_gen.py:264`), e isso pesa na comparação com o paper.

**16. Ordem dos campos e limites da resposta.** Vem da cópia do texto (linha 13), sem decisão nova. A
resposta traz a justificativa de cada KC antes do nome, como o paper descreve, "We instruct the model
to first explain the relevance of each KC, and then generate a clear textual description" (p. 33407
(PDF 3)), e o app pedia o contrário. Saem os limites do TCC 1, de 3 a 7 KCs por problema e de 3 a 8
palavras por nome (`candidate_generation.py:132-133` do app), porque no paper o nível de abstração é
controlado pelo agrupamento. Entram a definição de KC e a instrução de usar os exemplos como
referência de detalhe, que o prompt do TCC 1 não tinha.

**17. Validação da resposta.** O paper não trata. O repositório lê a resposta no modo JSON da OpenAI,
guarda só o nome de cada KC e, se um nome contém "KC", para no depurador (`KC_gen.py:155-162`). O app
valida a estrutura do JSON, com um nome e uma justificativa por KC, tenta de novo se ela vier
inválida e guarda a justificativa (critério 5).

#### O agrupamento e o nível de abstração

O segundo passo transforma o nome de cada KC num vetor com o Sentence-BERT e junta os parecidos com
HAC, "By adjusting the number of clusters, we can flexibly merge semantically similar KCs into
broader categories, effectively controlling the abstraction level of our KC descriptions" (p. 33407
(PDF 3)). Estes pontos são iguais no repositório e no app, e também no paper quando ele trata deles.

- O vetor de cada KC sai do SBERT `all-MiniLM-L6-v2` sobre o nome do KC, sem pedir normalização no
  código, e a distância cosseno não depende da norma (`KC_gen.py:324-325` e `600`;
  `kcgen_kt_generator.py:29` e `140` do app). O paper fala em "the
  Sentence-BERT (Reimers and Gurevych, 2019) embedding of the textual description of each KC"
  (p. 33407 (PDF 3)), sem dizer o modelo, e o repositório guarda só o nome. A versão da biblioteca é
  a 3.2.1 no repositório (`environment.yml:99`) e a 5.4.1 no app (`pyproject.toml:31`), com o mesmo
  modelo.
- O HAC é o do scipy, com distância cosseno, ligação média e corte em k grupos (`KC_gen.py:327-330`;
  `kc_grouping.py:16-19` do app). O paper diz "using cosine similarity as the distance function"
  (p. 33407 (PDF 3)) e, no Apêndice C, "we use scipy library to perform the hierarchical
  agglomerative clustering" (p. 33418 (PDF 14)), sem dizer a ligação.
- Nomes iguais entram uma vez só, pela comparação exata do texto (`KC_gen.py:596`;
  `kcgen_kt_generator.py:97-98` do app).

| # | Item | Paper | Repositório | TCC 1 | App antes | App depois | Origem |
|---|---|---|---|---|---|---|---|
| 18 | Escopo do agrupamento | todos os problemas do dataset juntos (p. 33406) | os 50 problemas da CodeWorkout juntos | cada exercício separado | cada exercício separado | cada exercício separado | app, critério 4 |
| 19 | Número de grupos | cinco níveis testados, e o médio escolhido pelo desempenho do modelo de KT, 50 grupos para 103 nomes na CodeWorkout (pp. 33410 e 33411) | 75 no `main()` | o maior silhouette entre 10, 12 e 15 | igual ao TCC 1 | a proporção do nível escolhido na CodeWorkout, 50 para 103, sobre os nomes do exercício | app, critério 4 |
| 20 | Poucos nomes | não trata | não trata | pula os candidatos que não ficam abaixo do número de nomes | com menos de 10 nomes cada um vira um grupo, e com exatamente 10 a extração falha | a mesma proporção, com pelo menos 1 grupo | app, critério 5 |
| 21 | Ordem de entrada dos nomes | não trata | a de um conjunto do Python, que muda a cada execução | a dos problemas em ordem numérica | a dos problemas em ordem de texto | a dos problemas em ordem numérica | app, critérios 3 e 5 |

**18. Escopo do agrupamento.** O paper agrupa os KCs "across all problems" e faz todos os passos
"independently for each dataset to maintain domain consistency" (p. 33406 (PDF 2)), e o repositório
junta os nomes dos 50 problemas da CodeWorkout num só conjunto (`KC_gen.py:596-600`). Os 50 problemas
são os dos cinco exercícios da CSEDM, então no paper os KCs parecidos dos cinco exercícios caem no
mesmo grupo e levam um nome só. O TCC 1 agrupava cada exercício à parte (notebook 03b, célula 12), e
o app também. O paper agrupa um dataset fechado, e a CodeWorkout é a de Spring 2019 (p. 33414
(PDF 10)). No app, o dado da turma chega durante a disciplina, a extração, a
aprovação e o treino são por exercício, e os conceitos de um exercício treinado não mudam
(`knowledge_component_edit.py:32-36` do app). Agrupar a turma inteira refaria os grupos a cada
exercício novo e mudaria os conceitos dos exercícios já aprovados e treinados. Pelo critério 4, o
app agrupa por exercício. O custo é o mesmo conceito aparecer com nomes diferentes em exercícios
diferentes, e ligar os conceitos entre exercícios fica para depois.

**19. Número de grupos.** O paper testa cinco níveis por dataset, 100, 75, 50, 20 e 10 grupos para
os 103 nomes da CodeWorkout e 150, 120, 90, 60 e 20 para os 161 da FalconCode (p. 33411 (PDF 7)), e
fica com o de melhor desempenho do modelo de KT, "50 KCs after clustering for CodeWorkout and 60 KCs
after clustering for FalconCode" (p. 33410 (PDF 6)). Na Tabela 3 (p. 33410 (PDF 6)), os níveis altos
são os piores, com AUC de 0,804 e 0,794 para 20 e 10 grupos na CodeWorkout, contra 0,816 para 50. O
paper não usa silhouette, e o repositório roda com 75 (`KC_gen.py:646`). O app não tem como escolher
pelo desempenho do modelo de KT, porque os conceitos não entram no Code-DKT. O TCC 1 escolhia pelo
maior silhouette entre 10, 12 e 15 (notebook 03b, célula 12), uma grade que não vem do paper. O
maior dos três venceu em quatro dos cinco exercícios, e a escolha deu 12 a 15 grupos para 52 a 59
nomes (`results/kc_clusters_A*.json` do TCC 1), entre 0,20 e 0,29 grupo por nome, perto do nível alto
da CodeWorkout (20 para 103, 0,19). Pelo critério 4, o app reproduz o nível que o paper escolheu na
CodeWorkout, que é Java como o app, com k igual a 50/103 dos nomes únicos do exercício, arredondado
para o inteiro mais próximo. O paper mediu essa proporção sobre os 50 problemas juntos, em que nomes
iguais de problemas diferentes se fundem antes do agrupamento. Por exercício, com 10 problemas, deve
sobrar mais nome por problema e sair mais conceito por exercício do que no paper, e o número de
conceitos por exercício é conferido depois da extração nova. A escolha do nível pelo professor, que o
paper apoia ao dizer que a abstração serve a "different pedagogical or analytical goals depending on
the downstream application" (p. 33407 (PDF 3)), fica para depois.

**20. Poucos nomes.** O app tinha um caminho à parte para menos de 10 nomes, em que cada nome vira um
grupo (`kcgen_kt_generator.py:101` do app). Com exatamente 10 nomes, nenhum candidato ficava abaixo
do total e a escolha do k falhava (`kc_grouping.py:27-31` do app). Com a proporção, o k sai do número
de nomes, com pelo menos um grupo, e os dois casos somem. Um nome só vira um grupo sem passar pelo
HAC, que precisa de pelo menos dois (critério 5).

**21. Ordem de entrada dos nomes.** A ordem em que os nomes entram no agrupamento não muda os grupos,
salvo empates nas distâncias, mas muda a numeração deles e o texto dos pedidos de nomeação, que faz
parte da chave do cache. O repositório tira os nomes de um conjunto do Python (`KC_gen.py:596-597`),
e a ordem muda a cada execução, um defeito de reprodutibilidade (critério 3). O TCC 1 percorria os
problemas em ordem numérica (notebook 03b, célula 12). O app os ordena como texto, com "10" antes de
"2", e o comentário do código e o `DECISIONS.md` dizem que isso é fiel ao TCC 1
(`kcgen_kt_generator.py:76-77` e `DECISIONS.md:105-107` do app), o que não é. O app passa a percorrer
os problemas em ordem numérica, e os nomes de cada problema na ordem da resposta do modelo
(critério 5).

#### A nomeação e a Q-matrix

O terceiro passo dá um nome a cada grupo, "We use a chain-of-thought prompt that guides the model to
first reason whether any KC in the cluster can represent the entire group. If such a KC exists, it is
selected as the cluster label; otherwise, the model is instructed to synthesize a concise description
that captures the shared meaning of KCs in the cluster" (p. 33407 (PDF 3)). Estes pontos são iguais
no repositório e no app, e também no paper quando ele trata deles.

- O pedido de nomeação recebe só os nomes dos KCs do grupo, sem enunciado, sem código e sem as
  justificativas (Tabela 10, p. 33422 (PDF 18); `KC_gen.py:341`; `group_naming.py:29-44` do app).
- A Q-matrix sai de trocar cada KC de um problema pelo nome do seu grupo, "by mapping each initially
  generated KC for each problem to its corresponding summarized cluster label" (p. 33407 (PDF 3)), e
  dois KCs do mesmo problema no mesmo grupo viram uma marca só (`KC_gen.py:530`;
  `qmatrix_builder.py:19-21` do app).

| # | Item | Paper | Repositório | TCC 1 | App antes | App depois | Origem |
|---|---|---|---|---|---|---|---|
| 22 | Texto do prompt de nomeação | Tabela 10 (p. 33422) | as palavras da Tabela 10 com três mudanças no terceiro passo e uma mensagem do usuário mais longa | próprio | igual ao TCC 1, salvo as chaves do modelo de JSON | o da Tabela 10 | Duan (paper) |
| 23 | Campos da resposta | a justificativa, o `representative kc` e o `summary name`, um dos dois nulo | os mesmos, com sublinhado nas chaves | `kc_id`, `name` e `reasoning` | igual ao TCC 1 | os da Tabela 10 | Duan (paper) |
| 24 | Grupo de um KC só | rotula cada grupo com o LLM, sem tratar o de um KC só (p. 33407) | sem chamada ao LLM, com o nome do KC | chama o LLM | chama o LLM nos grupos do HAC | igual ao repositório | Duan (repositório) |
| 25 | Caixa do nome em inglês | não trata | minúsculas | a que o modelo escreve | a que o modelo escreve | minúsculas | Duan (repositório) |
| 26 | Grupos com o mesmo nome | não trata | viram um KC só | ficam separados | ficam separados | viram um conceito só | Duan (repositório) |

**22. Texto do prompt de nomeação.** O paper mostra o prompt da nomeação na Tabela 10 (Apêndice G.1,
p. 33422 (PDF 18)). Ao contrário da geração (linha 13), o repositório não tem as mesmas palavras. No
terceiro passo, a tabela pede "a concise and meaningful summary name that captures the broader theme
or category shared by the KCs", e o repositório pede "a brief and meaningful summary name that
captures the broader theme shared by the KCs. The summary name must not contain the word “and”"
(`KC_gen.py:352`). A mensagem do usuário da tabela traz a lista e "Now follow the instructions in
system message and perform the task", e a do repositório repete os três passos (`KC_gen.py:341`). O
`KC_gen.py` tem um commit só (`ac017bc`, de 08/10/2025), e o ACL, de 2026, continua mostrando o texto
da tabela. Pelo critério 1, o app usa as palavras da Tabela 10. A lista vai no formato que o próprio
texto de sistema anuncia, ["KC 1 name", "KC 2 name", ..., "KC k name"], como o repositório faz com
`json.dumps` (critério 2). O TCC 1 reescreveu o prompt (notebook 03b, célula 15), com outro papel para
o modelo, a definição de KC com 3 a 8 palavras e o nome antes da justificativa, e o app o copiou
(`group_naming.py:8-44` do app), com chaves simples no modelo de JSON no lugar das duplas que o TCC 1
mandava, e com um comentário que o atribui à Tabela 9 de Duan et al. (2025)
(`group_naming.py:7` do app). A Tabela 9 da v3 é a 10 do ACL, e o texto é do TCC 1. Sem a proibição
do "and", o caso de KCs distintos demais fica com a regra do próprio paper, que manda criar um
nome-resumo do tema comum. Nos rótulos do TCC 1, 21 de 72 têm a palavra "and" em minúsculas
(`results/kc_descriptions_A*.json` do TCC 1). Os KCs gerados que o paper publica também têm, como
"If and else if statement" na Tabela 1 (p. 33406 (PDF 2)) e "Array indexing and assignment" na
Tabela 7 (p. 33419 (PDF 15)).

**23. Campos da resposta.** A Tabela 10 pede a justificativa em uma frase, o `representative kc`,
quando um KC da lista representa o grupo, e o `summary name`, quando nenhum representa, com o outro
nulo (p. 33422 (PDF 18)). O repositório usa as mesmas chaves com sublinhado e fica com o
representante ou, se ele for nulo, com o resumo (`KC_gen.py:357-358` e `376`). O TCC 1 e o app pedem
`kc_id`, `name` e `reasoning`, com o nome antes da justificativa (notebook 03b, célula 15;
`group_naming.py:18-26` do app), e não registram se o nome foi escolhido da lista ou criado. O app
passa a pedir os campos da Tabela 10, com as chaves dela, e a ficar com o representante ou, se ele
for nulo, com o resumo, como o repositório (critérios 1 e 2). A resposta é validada e repetida como na
linha 17, e se ainda falhar a extração para com erro (critério 3). O repositório devolve um nome
vazio (`KC_gen.py:382`), os KCs do grupo não entram no mapa dos nomes (`KC_gen.py:397-401`), e a
montagem do mapeamento dos problemas para com `KeyError` ao procurá-los (`KC_gen.py:530`).

**24. Grupo de um KC só.** O paper rotula cada grupo com o LLM, "we label each KC cluster by
prompting GPT-4o to generate a single, informative name that represents the cluster" (p. 33407
(PDF 3)), sem tratar à parte o grupo de um KC só. Pela regra do próprio paper, quando um KC
representa o grupo ele vira o nome do grupo, e um KC sozinho representa o grupo. O repositório só
chama o LLM para grupos com mais de um KC, e o grupo de um KC só fica com o nome dele
(`KC_gen.py:392-395`). O TCC 1 chama o LLM para todo grupo (notebook 03b, célula 15), e o app também
nos grupos que saem do HAC (`kcgen_kt_generator.py:147-154` do app). No caminho de menos de 10 nomes,
que sai com a linha 20, cada nome do app vira um grupo sem chamada. O app segue o repositório
(critério 2), que dá o nome que a regra do paper daria, com menos chamadas.

**25. Caixa do nome em inglês.** O paper não trata. Os exemplos dele aparecem com maiúscula na Tabela
1 (p. 33406 (PDF 2)) e em minúsculas na entrada da Tabela 10. O repositório passa todo nome de grupo
para minúsculas (`KC_gen.py:378` e `395`), e o app guardava a caixa que o modelo escrevia. Pelo
critério 2, o app segue o repositório. O nome em inglês é o registro do método, e o professor lê a
tradução em português, com a caixa normal.

**26. Grupos com o mesmo nome.** O paper não trata. No repositório, o KC é o próprio texto do nome,
então dois grupos que recebem o mesmo nome viram um KC só no mapeamento dos problemas
(`KC_gen.py:401` e `530`). O TCC 1 e o app guardam um conceito por grupo, mesmo com o nome repetido
(`kcgen_kt_generator.py:158` do app). Pelo critério 2, o app segue o repositório, e a comparação dos
nomes é feita depois da passagem para minúsculas (linha 25). Na Q-matrix, as colunas dos dois grupos
viram uma.

### Seções 3 a 5 do paper, a avaliação

O paper avalia os KCs gerados pelo desempenho do seu modelo de KT (§3 e §4.1), pelas curvas de
aprendizagem (§4.2) e com dois anotadores (§5). O app não tem o modelo de KT do paper, e a extração
é conferida por testes e por uma comparação com o que o paper publica.

| # | Item | Paper | Repositório | TCC 1 | App antes | App depois | Origem |
|---|---|---|---|---|---|---|---|
| 27 | Regressão das partes sem LLM | não tem | não tem | não tem | testes do agrupamento e da Q-matrix com os artefatos do TCC 1 para o A439 | testes com a mesma entrada e a mesma saída no sorteio, no agrupamento, na Q-matrix e na ordem, com artefatos da extração nova | app, critério 5 |
| 28 | Regressão da extração inteira | não tem | não tem | o cache por exercício | o cache por chamada ao LLM, guardado por exercício, sem teste da extração inteira | um teste que repete a extração de referência pelo cache gravado, sem gastar cota | app, critério 5 |
| 29 | Comparação com o paper | os KCs gerados de dois problemas e a avaliação de dois anotadores com a rubrica do Apêndice F | um `problem_kc.json` de março de 2025, que não bate com a Tabela 1 | não tem | não tem | os KCs dos mesmos dois problemas lado a lado e a anotação do A439 com a mesma rubrica | app, critério 5 |

**27. Regressão das partes sem LLM.** O paper e o repositório não têm testes. O app tinha testes do
agrupamento e da Q-matrix com os artefatos do TCC 1 para o A439 (`kc_grouping_test.py`,
`qmatrix_builder_test.py` e `tests/fixtures/ml.py:17-20` do app), que deixam de valer com as decisões
1 a 26. Com a mesma entrada, o sorteio das soluções, o agrupamento dos nomes, a Q-matrix e a ordem
dos problemas têm que dar a mesma saída, e os artefatos de referência saem da extração nova. Esses
testes pegam uma mudança de comportamento sem chamar o LLM, como a de uma versão nova das bibliotecas
do CodeBERT e do SBERT, no papel que o teste de regressão tem no Code-DKT (critério 5).

**28. Regressão da extração inteira.** O app não tem como fixar a temperatura (linha 10), então a
extração inteira só se repete pelo cache das respostas do LLM. As respostas da extração de
referência da CSEDM, feita nos cinco exercícios e com os enunciados, ficam gravadas como dado de
teste. Um teste repete a
extração lendo o cache, sem gastar cota, e confere os nomes e a Q-matrix. A chave do cache inclui o
texto dos prompts (`llm_response_cache.py:23-40` do app), então mudar um prompt faz o teste falhar
por falta de resposta gravada (critério 5).

**29. Comparação com o paper.** O paper não publica a lista completa de KCs gerados, então não há um
valor de referência como o first-attempt AUC do Code-DKT. O repositório traz um `problem_kc.json`,
de março de 2025 e anterior ao `KC_gen.py`, com os KCs dos 50 problemas, mas ele não bate com o
paper. No love6, ele tem 7 KCs e 5 rótulos, e nenhum é igual aos nomes da Tabela 1. O paper publica
os KCs gerados de dois problemas, o love6 (A439, problema 233, Tabela 1, p. 33406 (PDF 2)) e o has77
(A494, problema 67, Tabela 7, p. 33419 (PDF 15)). O exemplo de prompt da Tabela 11 (p. 33423
(PDF 19)) traz ainda quatro KCs do sortaSum (A439, problema 1), sem dizer se são os gerados. O paper
também publica a avaliação de dois anotadores nos 50 problemas da CodeWorkout (§5, p. 33413
(PDF 9)), com a rubrica do Apêndice F (p. 33418 (PDF 14)). Nela, 98,6% dos
KCs gerados foram julgados interpretáveis, contra 94,6% das tags humanas, a precisão dos vínculos
entre problema e KC foi de 93,2%, contra 92,5%, e os KCs gerados cobriram tanto quanto as tags
humanas ou mais em 96% dos problemas. A comparação do app é um relatório, e não um teste que passa ou
falha, gravado em `docs/results` como o do Code-DKT. Ele põe os KCs do love6 e do has77 ao lado dos
do paper e traz a anotação do A439, feita pelo autor do TCC com a mesma rubrica, contra as 18 tags
humanas da planilha oficial. O problema 13 do A439 entra marcado, porque os KCs humanos dele estão no
prompt (linha 15). Com um anotador só, não há a medida de concordância que o paper reporta
(critério 5).

#### Fora do escopo

- **O modelo de KT do paper.** O KCGen-KT do paper é um modelo de KT que usa o Llama 3 e estima a
  maestria de cada KC (§2.2, pp. 33407 a 33409 (PDF 3 a 5)), com 8B de parâmetros (§3, p. 33410
  (PDF 6)). O app usa o Code-DKT, e os
  conceitos não entram no treino. A principal evidência do paper a favor dos KCs gerados foi medida
  com esse modelo, um AUC de 0,816 na CodeWorkout, contra 0,797 com as tags humanas e 0,766 do
  Code-DKT (Tabela 2, p. 33410 (PDF 6)), e não vale para o app. O domínio por conceito do app é a
  média do domínio dos problemas que exigem o conceito, e não a maestria do paper (O que o app
  acrescenta ao Code-DKT).
- **A rotulagem de erro por KC e as curvas de aprendizagem.** O paper pede ao GPT-4o um rótulo de erro
  por KC nas submissões incorretas (Tabela 11) para traçar as curvas (§4.2). A curva do paper conta
  como oportunidade cada problema em que o aluno pratica o KC, "the problem that represents their
  t-th attempt at the KC" (p. 33412 (PDF 8)), sobre as primeiras submissões (§3, p. 33409 (PDF 5)).
  A curva do app é do painel, conta cada execução como oportunidade (`DECISIONS.md:531-535` do app)
  e é revista quando o painel for implementado.
- **O FalconCode e os vários níveis de abstração.** O app só lê Java e usa um nível de abstração por
  exercício, sem a ontologia entre níveis da Figura 4.

### O que o app acrescenta ao KCGen-KT

- **A revisão pelo professor.** O ACL recomenda que especialistas revisem os KCs gerados antes do uso
  real, "we recommend that automatically generated KCs be reviewed by domain experts before
  deployment in real educational settings" (p. 33414 (PDF 10)), sem dizer como. No app, o exercício
  fica em rascunho até o professor aprovar os conceitos, e só a aprovação libera o treino
  (`approve_knowledge_components_use_case.py:49` e `start_training_use_case.py:41` do app). A v3 não
  tem essa recomendação.
- **Onde cada conceito aparece nas soluções.** Depois do agrupamento, na mesma extração, uma segunda
  chamada ao mesmo modelo recebe, para cada problema, as soluções que o LLM leu e os conceitos
  finais do problema. Ela devolve, para cada conceito, a solução e o trecho de código copiado dela.
  O app confere se o trecho existe na solução, guarda as linhas e descarta o trecho que não existe.
  A chamada é separada para que o prompt do Duan fique intacto, e ela aponta os conceitos finais,
  que são os que o professor vê, e não os KCs de antes do agrupamento. O trecho é a justificativa
  que o modelo escreve, e não a causa da extração, e a tela o mostra como o lugar onde o conceito
  aparece. A justificativa de uma frase que o prompt do Duan pede para cada KC, "a one-sentence
  reasoning explaining why this KC is necessary based on the provided solutions" (Tabela 9, p. 33421
  (PDF 17)), também passa a ser guardada e mostrada. Decidido em 03/10/2026, a implementar.
- **Os nomes em português.** O método roda em inglês, como no paper, com os prompts do Duan e, no
  agrupamento, o SBERT `all-MiniLM-L6-v2` do repositório, que é um modelo de inglês. Depois da
  nomeação, uma chamada ao mesmo modelo traduz para o português todos os nomes finais do exercício de
  uma vez, para que o mesmo termo saia igual em todos os conceitos, e na mesma chamada as
  justificativas de cada KC que a origem do conceito mostra. O app guarda o nome em inglês, que é o
  resultado do método, e o nome em português, que a tela mostra e o professor pode renomear.
  Decidido em 03/10/2026, a implementar.
- **Os problemas sem conceito.** Um problema sem nenhuma execução correta não tem solução para o LLM
  ler e fica sem conceito. O paper não trata, e o repositório e o TCC 1 o deixam de fora sem aviso. O
  app também, porque a lista de problemas sai das execuções corretas (`kcgen_kt_generator.py:75-77` do
  app) e a conferência só olha os problemas gerados (`knowledge_component_generator.py:24-32` do app).
  Durante a disciplina, é o caso do problema que ninguém acertou ainda. A extração passa a gerar os
  conceitos dos outros problemas e a listar para o professor os que ficaram sem conceito, com o
  motivo. Decidido em 03/10/2026, a implementar.

### Estado

| # | Estado |
|---|---|
| 1 a 29 | Decididas em 03/10/2026, a implementar pelo `KCGEN_KT_PLAN.md`, aprovado em 04/10/2026 |

## Referências

ALON, U.; ZILBERSTEIN, M.; LEVY, O.; YAHAV, E. code2vec: learning distributed representations of
code. Proceedings of the ACM on Programming Languages, v. 3, n. POPL, 2019.

DUAN, Z. et al. Automated Knowledge Component Generation for Interpretable Knowledge Tracing in
Coding Problems. arXiv:2502.18632v3, 2025.

DUAN, Z. et al. Automated Knowledge Component Generation and Interpretable Knowledge Tracing in
Coding Problems. In: Findings of the Association for Computational Linguistics: ACL 2026. 2026.
p. 33405–33423. Disponível em: https://aclanthology.org/2026.findings-acl.1670/.

FENG, Z. et al. CodeBERT: A Pre-Trained Model for Programming and Natural Languages. In: Findings
of the Association for Computational Linguistics: EMNLP 2020. 2020. p. 1536–1547.

GUO, D. et al. GraphCodeBERT: Pre-training Code Representations with Data Flow. In: International
Conference on Learning Representations (ICLR 2021). 2021.

PIECH, C. et al. Deep Knowledge Tracing. In: Advances in Neural Information Processing Systems 28
(NIPS 2015). 2015.

SHI, Y.; CHI, M.; BARNES, T.; PRICE, T. Code-DKT: A Code-based Knowledge Tracing Model for
Programming Tasks. In: Proceedings of the 15th International Conference on Educational Data Mining
(EDM 2022). Durham: International Educational Data Mining Society, 2022. p. 50–61. DOI
10.5281/zenodo.6853105.

SRIVASTAVA, N. et al. Dropout: a simple way to prevent neural networks from overfitting. Journal of
Machine Learning Research, v. 15, p. 1929–1958, 2014.
