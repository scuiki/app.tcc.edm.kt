<p align="center">
  <a href="https://github.com/scuiki/app.tcc.edm.kt/actions/workflows/testes.yml"><img src="https://github.com/scuiki/app.tcc.edm.kt/actions/workflows/testes.yml/badge.svg" alt="Testes"></a>
  <a href="https://doi.org/10.51189/conaiduc/83301"><img src="https://img.shields.io/badge/DOI-10.51189%2Fconaiduc%2F83301-blue" alt="DOI 10.51189/conaiduc/83301"></a>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/PyTorch-2.7.1-EE4C2C?logo=pytorch&logoColor=white" alt="PyTorch 2.7.1">
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" alt="React 19">
</p>

## Sobre o projeto

Ferramenta web para o professor de programação introdutória ver, durante a disciplina, quais
conceitos a turma ainda não domina, a partir dos envios de código da própria turma.

- **Importação ProgSnap2**: os envios de código Java da turma, num `.zip`.
- **Conceitos por LLM**: o KCGen-KT (Duan et al., 2026) extrai os conceitos de cada exercício, e o
  professor os revisa.
- **Code-DKT por turma**: o modelo de Shi et al. (2022) é treinado nos dados da turma, na GPU ou na
  CPU.
- **Domínio por conceito**: o domínio de cada aluno em cada conceito, ao lado das execuções por
  problema.
- **Reprodutível**: testes de regressão travam o resultado dos dois métodos.

## *About the project*

*A web tool that shows introductory programming instructors, during the course, which concepts
their class has not mastered yet, based on the class's own code submissions.*

- ***ProgSnap2 import:*** *the class's Java submissions, in a `.zip`.*
- ***Concepts by LLM:*** *KCGen-KT (Duan et al., 2026) extracts the concepts of each exercise, and
  the instructor reviews them.*
- ***Code-DKT per class:*** *the model by Shi et al. (2022) is trained on the class's data, on GPU
  or CPU.*
- ***Mastery per concept:*** *each student's mastery of each concept, next to the runs per
  problem.*
- ***Reproducible:*** *regression tests lock the results of both methods.*

## Instalação

### Requisitos

- Docker com o Compose (imagem `amd64`, cerca de 15 GB)
- Credencial do Claude, o token da assinatura (`claude setup-token`) ou uma chave da API
- GPU NVIDIA com o [NVIDIA Container
  Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html),
  opcional

### Como rodar

```bash
git clone https://github.com/scuiki/app.tcc.edm.kt.git
cd app.tcc.edm.kt
cp .env.example .env    # a credencial e, com GPU, o COMPOSE_FILE
docker compose up -d --build
```

O app abre em <http://127.0.0.1:5173>.

<details>
  <summary>Dados para experimentar</summary>
  <br>

O app recebe um `.zip` ProgSnap2 com o `MainTable.csv` e o `CodeStates.csv`. A CSEDM, variante
CodeWorkout de Spring 2019, do 2nd CSEDM Data Challenge, está no
[PSLC DataShop](https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=3458), com cadastro
gratuito. É também a usada pelos testes de regressão e pelos resultados em `docs/results`, e não
vem no repositório.

</details>

## Publicações

<img src="docs/assets/unifacens.png" alt="UniFacens" height="28">

**Monografia.** VIANA, E. M.; OLIVEIRA, L. K.; BORBA, V. S. *Análise do aprendizado de programação
utilizando mineração de dados educacionais*. Trabalho de Conclusão de Curso (Engenharia de
Computação), UniFacens, Coordenadoria de Engenharia da Computação, Sorocaba, 2026. 103 f.
Orientadora: Profa. Ma. Talita dos Reis Lopes Berbel.

<img src="docs/assets/conaiduc.png" alt="CONAIDUC" height="40">

**Resumo expandido.** OLIVEIRA, L. K.; VIANA, E. M.; BORBA, V. S.; BERBEL, T. R. L. *Identificação
de padrões de aprendizagem em programação por meio da análise de códigos de estudantes e da
mineração de dados educacionais*. I Congresso Nacional de Inovação em Educação, Ciência e
Tecnologia (CONAIDUC), on-line, 6 a 9 de julho de 2026. ISBN 9786588884621. DOI
[10.51189/conaiduc/83301](https://doi.org/10.51189/conaiduc/83301).

## Estrutura

```
src/ml/        o Code-DKT e o KCGen-KT, em PyTorch, sem depender do app
src/api/       a API em FastAPI e SQLite, organizada por funcionalidade
src/web/       a interface em React e TypeScript
tests/         testes de regressão, comparação com o paper e dados de teste
experiments/   BKT e DKT no mesmo protocolo do Code-DKT
docs/          arquitetura, decisões, desenvolvimento dos métodos e resultados
deploy/        a imagem da interface
```

Veja também o [`ARCHITECTURE.md`](docs/ARCHITECTURE.md), o [`DEVELOPMENT.md`](docs/DEVELOPMENT.md),
com a fidelidade aos dois métodos, os testes e a reprodução, e o
[`DECISIONS.md`](docs/DECISIONS.md).

## Licença

A definir.
