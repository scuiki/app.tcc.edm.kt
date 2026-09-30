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
  `8ddd13e`. Os arquivos e as linhas citados são desse commit.
- **Padrões citados pelo paper.** Para o que não especifica, o paper diz "All other parameters were
  defaulted as the original settings of code2vec and DKT" (p. 55 (PDF 6)). O code2vec é Alon et al.
  (2019), com o repositório [tech-srl/code2vec](https://github.com/tech-srl/code2vec), commit
  `77637c5`. O DKT é Piech et al. (2015).
- **TCC 1.** [scuiki/tcc.edm.kt](https://github.com/scuiki/tcc.edm.kt), commit `0e8807c`, com o
  notebook `notebooks/06_code_dkt.ipynb` e o `src/models/code_dkt.py`, de onde o código do app foi
  portado.

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

Estes pontos são iguais no paper, no repositório e no app, e não pediram decisão.

- O problema faz o papel do KC, "We use problemIDs for KCs in this work" (p. 52 (PDF 3), nota 1).
- O modelo prevê a próxima tentativa, e só a saída do próximo problema entra no treino e na
  avaliação (p. 53 (PDF 4)).
- A entrada do DKT é o one-hot de tamanho 2M, com a posição q_t + M(1 − a_t) ligada (p. 53 (PDF 4)).
- O LSTM, que o paper usa no lugar do RNN simples, parte do estado zerado (p. 53 (PDF 4)) e tem
  uma camada, como no repositório (`src/config.py:9`).
- Os paths vão de folha a folha na AST, como no code2vec (p. 53 (PDF 4)). O parser é o javalang,
  e os limites de 8 de comprimento e 2 de largura vêm do repositório (`src/config.py:12-13`), que
  repete os do code2vec (`preprocess.sh:42-48` do repositório dele).
- Cada path tem o nó inicial, o caminho e o nó final, e as duas folhas fazem parte do caminho, como
  em input|method|body|String|value (p. 53 (PDF 4)).
- O embedding de nó é compartilhado entre o início e o fim do path, e o de path é separado, os dois
  com inicialização gaussiana (p. 54 (PDF 5)). Cada um tem 100 dimensões
  (`src/c2vRNNModel.py:14-15`), e os três somam os 300 do "embedding size of code feature
  extraction" (p. 55 (PDF 6)).
- O x_t entra em cada e_r e de novo na entrada do LSTM (p. 54 (PDF 5)).
- O dropout de 0,2 nos embeddings durante o treino vem do repositório (`src/c2vRNNModel.py:16`). O
  paper não fala dele.
- O código concatena na ordem início, fim e path, e o paper escreve início, path e fim (p. 54
  (PDF 5)). A ordem muda só a posição dos números no vetor, e não o que o modelo consegue aprender.

#### As decisões

| # | Item | Paper | Repositório | TCC 1 | App antes | App depois |
|---|---|---|---|---|---|---|
| 1 | Quais paths entram | R sorteados (p. 53), sem valor para R | os 100 primeiros, sem sorteio | 50 sorteados, seed 42 | 50 sorteados, seed 42 | 100 sorteados, seed 42 |
| 2 | Ordem dos modificadores Java | não trata | a do `set`, que muda a cada processo | igual ao repositório | igual ao repositório | igual ao repositório, com `PYTHONHASHSEED=0` |
| 3 | Token fora do vocabulário | não trata | índice próprio | o 0 do preenchimento | o 0 do preenchimento | índice próprio |
| 4 | Nota da atenção | α = SoftMax(E·W_a) (p. 54) | camada com tanh antes da nota | igual ao repositório | igual ao repositório | igual ao repositório |
| 5 | Eixo do softmax | os R paths (p. 54) | o tempo | os R paths | os R paths | os R paths |
| 6 | W_0 depois da soma ponderada | z = W_0(Σ α_i e_i) (p. 54) | não tem | não tem | não tem | incluído, de 320 para 320 |
| 7 | Dropout na saída do LSTM | não trata | criado e nunca usado | 0 no padrão, 0,1 na grade | 0,1 | nenhum |
| 8 | Dropout dos embeddings na avaliação | não trata | ligado | desligado | desligado | desligado |

#### Justificativas

**1. Quais paths entram.** O paper representa cada solução por "R randomly selected code paths"
(p. 53 (PDF 4)) e não dá o valor de R. O repositório usa R=100 (`src/readdata.py:55`), mas pega os
100 primeiros da lista, sem sorteio (`src/readdata.py:140`). A lista segue a ordem em que os pares de
folhas são percorridos, primeiro todos os paths da primeira folha e depois os da segunda, então os
primeiros se concentram no começo do método, na assinatura. O app segue o paper no sorteio e o
repositório no valor (critérios 1 e 3). O padrão do code2vec é 200 (`config.py:60` do repositório
dele), e pelo critério 3 vale o repositório. A seed 42 só fixa o sorteio, e o valor é o do TCC 1 e
do resto do app (critério 5). O TCC 1 usava R=50 e atribuía o valor à Tabela 3 do paper (notebook
06, célula 3, e `docs/code_dkt_implementation.md:175`), mas a Tabela 3 é o desempenho por problema
(p. 56 (PDF 7)), e a faixa (30, 50, 100, 300) que ele cita é a do número de features do TF-IDF de um
baseline (p. 55 (PDF 6)).

**2. Ordem dos modificadores Java.** O javalang devolve os modificadores de uma declaração, como
`public` e `static`, num conjunto do Python, e o repositório transforma esse conjunto em lista com
`list(root)` (`src/path_extractor.py:28`). A ordem de um conjunto de textos depende da semente de
hash que o Python sorteia a cada processo, então a mesma solução gera paths diferentes em processos
diferentes. No A439 isso fazia o first-attempt AUC alternar entre 0,7595 e 0,7608. O paper não trata
do assunto, então o app mantém o código do repositório (critério 3) e fixa a variável de ambiente
`PYTHONHASHSEED=0` nas imagens (critério 5). A ordem passa a ser sempre a mesma sem mudar o método,
inclusive entre reinícios do container e imagens novas, enquanto a versão do Python for a mesma, e a
imagem fixa o Python 3.11. Fixar o hash tira da api a proteção contra hash flooding, um ataque que
manda chaves com o mesmo hash para travar o processo. O risco é desprezível, porque a api não
publica porta e o app tem um usuário numa rede privada.

**3. Token fora do vocabulário.** Um nó ou path que aparece no teste e não apareceu no treino
precisa de um índice. O repositório reserva o 0 para o preenchimento das posições vazias e o 1 para
o desconhecido (`src/readdata.py:18-19`). O TCC 1 e o app usavam o 0 para os dois
(`src/ml/code_dkt/model_input.py:22-24` do app), e o modelo não distinguia uma posição vazia de um
path desconhecido. No TCC 1, 6,0% dos paths do teste do A439 eram desconhecidos (notebook 06,
célula 15). O app passa a seguir o repositório (critério 3).

**4. Nota da atenção.** A equação do paper calcula a nota de cada path como uma combinação linear
do vetor dele, α = SoftMax(E·W_a) (p. 54 (PDF 5)). O repositório passa o vetor antes por uma camada
linear com tanh e só então calcula a nota (`src/c2vRNNModel.py:17-18` e `56-57`), como faz o
code2vec (`tensorflow_model.py:252-254` do repositório dele), de onde o paper diz que a estrutura
veio (p. 54 (PDF 5)). A diferença importa porque cada e_r carrega o x_t, que é o mesmo em todos os
paths da mesma tentativa. Na versão linear, a parte da nota que vem do x_t é a mesma parcela somada a
todas as notas, e o softmax não muda quando se soma o mesmo valor a todas elas, então o acerto não
influencia os pesos. Com o tanh, o x_t se combina com o código de cada path antes da nota. O paper
chama esse passo de "Score-Attended Path Selection" e diz que o e_r inclui o acerto para orientar a
escolha dos paths (p. 54 (PDF 5)), o que só a versão do repositório faz. O app mantém a versão do
repositório (critério 2), e a equação do paper é lida como uma notação simplificada.

**5. Eixo do softmax.** O paper normaliza as notas sobre os R paths de cada tentativa, com a soma de
1 a R no denominador (p. 54 (PDF 5)). O repositório usa `Softmax(dim=1)` (`src/c2vRNNModel.py:21`)
num tensor de forma (lote, tempo, paths, 1), o que normaliza sobre o tempo. Assim a atenção de um
passo depende dos passos seguintes do mesmo aluno, inclusive da tentativa que o modelo deveria
prever. O eixo 1 é provavelmente herança do code2vec, em que o tensor não tem o tempo e o eixo 1 é o
dos paths (`tensorflow_model.py:260` do repositório dele). O TCC 1 já usava o eixo dos paths
(`src/models/code_dkt.py:91`), e o app mantém (critério 4).

**6. W_0.** O paper multiplica a média ponderada dos paths por uma matriz W_0 para obter o vetor de
código z, e isso aparece no texto, na equação e na Figura 3, como "Linear Layer W_0" (p. 54
(PDF 5)). O repositório não tem essa camada e manda a média ponderada direto para o LSTM
(`src/c2vRNNModel.py:59-60`). O TCC 1 também não tem, e a documentação dele chamava de W_0 a camada
com tanh da atenção (`docs/code_dkt_implementation.md:320-321`), que é outra. O app inclui o W_0
(critério 1) como uma camada linear de 320 para 320, porque o paper não dá o tamanho de z
(critério 5). A primeira operação do LSTM sobre a entrada também é linear, e duas operações lineares
seguidas equivalem a uma. Por isso o W_0 não aumenta o que o modelo consegue representar, e muda só
o número de parâmetros e o caminho do treino.

**7. Dropout na saída do LSTM.** O paper não fala desse dropout. O repositório cria a camada com 0,1
(`src/c2vRNNModel.py:32`), mas a linha que a usaria está comentada (`src/c2vRNNModel.py:65-66`). O
DKT aplica dropout na passagem de h_t para a saída y_t, sem dar a taxa (Piech et al., 2015,
subseção Optimization), e pelo critério 3 vale o repositório, que desligou essa camada. O 0,1 do app
veio da melhor configuração da grade do TCC 1 (notebook 06, célula 24). Nessa grade, com hidden de
128, a versão sem dropout foi até um pouco melhor na validação (0,7196 contra 0,7148, numa seed só),
uma diferença do tamanho do ruído.

**8. Dropout dos embeddings na avaliação.** O dropout serve ao treino, e na avaliação a prática é
desligá-lo, para que a mesma entrada dê sempre a mesma previsão (Srivastava et al., 2014). O
repositório tem o parâmetro `evaluating` para desligar o dropout dos embeddings
(`src/c2vRNNModel.py:36` e `53-54`), mas a avaliação nunca o passa (`src/evaluation.py:219`) nem
chama `model.eval()`, e o dropout fica ligado no teste. Ligado, cada previsão descarta 20% dos
valores ao acaso, o AUC carrega esse ruído, e o domínio do painel mudaria a cada cálculo. O dropout
de Monte Carlo mantém o dropout ligado de propósito, mas repete a previsão muitas vezes e tira a
média, o que o repositório não faz. O TCC 1 e o app desligam o dropout na avaliação
(`src/ml/code_dkt/prediction.py:32` do app), e isso fica registrado como correção de um defeito do
repositório (critério 4).

### Seção 4 do paper, dados e experimento

A discutir. Os pontos já levantados estão abaixo.

- Os eventos que entram, só `Run.Program`, e o rótulo, correto quando todos os testes passam
  (p. 54 (PDF 5)).
- A ordem das execuções. O repositório lê na ordem do arquivo, agrupada por problema, e o app ordena
  por tempo.
- O truncamento nas últimas 50 submissões (p. 55 (PDF 6)) e a definição de primeira tentativa.
- A partição 4:1 por exercício (p. 54 (PDF 5)) e o filtro de alunos com pelo menos três tentativas,
  que vem do TCC 1.
- Os hiperparâmetros. O paper declara embedding de 300, taxa de aprendizado de 0,0005 e 40 épocas
  (p. 55 (PDF 6)) e manda usar os padrões do code2vec e do DKT no resto. O DKT usa hidden de 200,
  lote de 100, dropout na saída e corte de gradiente (Piech et al., 2015), e o repositório usa hidden
  de 128, lote de 128 e nenhum corte.
- As dez execuções (p. 55 (PDF 6)) e o oráculo, com a meta de 75,74% de first-attempt AUC no A1
  (Tabela 2, p. 55 (PDF 6)) e o AUC geral dos cinco exercícios (Tabela 1, p. 55 (PDF 6)).

### Estado

| # | Estado |
|---|---|
| 1 | Decidida em 30/09/2026, não implementada. O TCC 1 mediu 2,2 GB de VRAM com R=50, e o R=100 será medido na implementação |
| 2 | Decidida em 30/09/2026, não implementada |
| 3 | Decidida em 30/09/2026, não implementada |
| 4 | Decidida em 30/09/2026, sem mudança no código |
| 5 | Decidida em 30/09/2026, sem mudança no código |
| 6 | Decidida em 30/09/2026, não implementada |
| 7 | Decidida em 30/09/2026, não implementada |
| 8 | Decidida em 30/09/2026, sem mudança no código |

## KCGen-KT

A discutir, depois do Code-DKT.

### Fontes

- **Paper.** Duan et al. (2025), na versão 2502.18632v3 do arXiv, que o TCC 1 usou, e na versão
  publicada no ACL 2026 Findings, segundo o repositório oficial.
- **Repositório oficial.** [umass-ml4ed/kcgen-kt](https://github.com/umass-ml4ed/kcgen-kt).
- **TCC 1.** O notebook `notebooks/03b_kc_generation.ipynb`.

## Referências

ALON, U.; ZILBERSTEIN, M.; LEVY, O.; YAHAV, E. code2vec: learning distributed representations of
code. Proceedings of the ACM on Programming Languages, v. 3, n. POPL, 2019.

DUAN, Z. et al. Automated Knowledge Component Generation for Interpretable Knowledge Tracing in
Coding Problems. arXiv:2502.18632v3, 2025.

PIECH, C. et al. Deep Knowledge Tracing. In: Advances in Neural Information Processing Systems 28
(NIPS 2015). 2015.

SHI, Y.; CHI, M.; BARNES, T.; PRICE, T. Code-DKT: A Code-based Knowledge Tracing Model for
Programming Tasks. In: Proceedings of the 15th International Conference on Educational Data Mining
(EDM 2022). Durham: International Educational Data Mining Society, 2022. p. 50–61. DOI
10.5281/zenodo.6853105.

SRIVASTAVA, N. et al. Dropout: a simple way to prevent neural networks from overfitting. Journal of
Machine Learning Research, v. 15, p. 1929–1958, 2014.
