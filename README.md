<p align="center">
  <a href="https://github.com/scuiki/app.tcc.edm.kt/actions/workflows/testes.yml"><img src="https://github.com/scuiki/app.tcc.edm.kt/actions/workflows/testes.yml/badge.svg" alt="Tests"></a>
  <a href="https://doi.org/10.51189/conaiduc/83301"><img src="https://img.shields.io/badge/DOI-10.51189%2Fconaiduc%2F83301-blue" alt="DOI 10.51189/conaiduc/83301"></a>
</p>

## Sobre o projeto

Uma ferramenta web que auxilia o professor de programação a acompanhar o processo de aprendizagem
de sua turma, a partir dos códigos submetidos por seus estudantes.

<details>
  <summary><em>English version</em></summary>
  <br>

*A web tool that helps programming instructors follow the learning process of their class, based on
the code submitted by their students.*

</details>

## Stack

<p>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11">
  <img src="https://img.shields.io/badge/PyTorch-2.7.1-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch 2.7.1">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/Claude-Haiku_4.5-D97757?style=for-the-badge&logo=claude&logoColor=white" alt="Claude Haiku 4.5">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 19">
  <img src="https://img.shields.io/badge/TypeScript-6-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript 6">
  <img src="https://img.shields.io/badge/Vite-8-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite 8">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

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
  <summary>Dados de entrada</summary>
  <br>

- **Formato**: `.zip` ProgSnap2 com `MainTable.csv` e `CodeStates.csv`.
- **Exemplo**: CSEDM, variante CodeWorkout (Spring 2019), do 2nd CSEDM Data Challenge, no
  [PSLC DataShop](https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=3458) (cadastro gratuito).

</details>

<details>
  <summary><em>English version</em></summary>
  <br>

***Requirements***

- *Docker with Compose (`amd64` image, about 15 GB)*
- *A Claude credential, either a subscription token (`claude setup-token`) or an API key*
- *An NVIDIA GPU with the [NVIDIA Container
  Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html),
  optional*

***Running***

```bash
git clone https://github.com/scuiki/app.tcc.edm.kt.git
cd app.tcc.edm.kt
cp .env.example .env    # the credential and, with a GPU, COMPOSE_FILE
docker compose up -d --build
```

*The app opens at <http://127.0.0.1:5173>.*

***Input data***

- ***Format:*** *a ProgSnap2 `.zip` with `MainTable.csv` and `CodeStates.csv`.*
- ***Example:*** *CSEDM, CodeWorkout variant (Spring 2019), from the 2nd CSEDM Data Challenge, on
  [PSLC DataShop](https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=3458) (free sign-up).*

</details>

## Publicações

<img src="docs/assets/unifacens.png" alt="UniFacens" height="40">

**Monografia.** VIANA, E. M.; OLIVEIRA, L. K.; BORBA, V. S. *Análise do aprendizado de programação
utilizando mineração de dados educacionais*. Trabalho de Conclusão de Curso (Engenharia de
Computação), UniFacens, Coordenadoria de Engenharia da Computação, Sorocaba, 2026. 103 f.
Orientadora: Profa. Ma. Talita dos Reis Lopes Berbel.

<img src="docs/assets/conaiduc.png" alt="CONAIDUC" height="60">

**Resumo expandido.** OLIVEIRA, Leonardo Kuntz; VIANA, Erick Miranda; BORBA, Victor Santos; BERBEL,
Talita dos Reis Lopes. Identificação de padrões de aprendizagem em programação por meio da análise
de códigos de estudantes e da mineração de dados educacionais. In: CONGRESSO NACIONAL DE INOVAÇÃO
EM EDUCAÇÃO, CIÊNCIA E TECNOLOGIA, 1., 2026, On-line. Anais [...]. [S. l.]: Editora Integrar, 2026.
DOI: 10.51189/conaiduc/83301. Disponível em:
<https://doi.org/10.51189/conaiduc/83301>.

<details>
  <summary><em>English version</em></summary>
  <br>

***Monograph.*** *VIANA, E. M.; OLIVEIRA, L. K.; BORBA, V. S. Análise do aprendizado de
programação utilizando mineração de dados educacionais. Undergraduate thesis (Computer
Engineering), UniFacens, Sorocaba, 2026. 103 p. Advisor: Profa. Ma. Talita dos Reis Lopes Berbel.*

***Extended abstract.*** *OLIVEIRA, Leonardo Kuntz; VIANA, Erick Miranda; BORBA, Victor Santos; BERBEL,
Talita dos Reis Lopes. Identificação de padrões de aprendizagem em programação por meio da análise
de códigos de estudantes e da mineração de dados educacionais. In: CONGRESSO NACIONAL DE INOVAÇÃO
EM EDUCAÇÃO, CIÊNCIA E TECNOLOGIA, 1., 2026, On-line. Anais [...]. [S. l.]: Editora Integrar, 2026.
DOI: 10.51189/conaiduc/83301. Disponível em:
<https://doi.org/10.51189/conaiduc/83301>.*

</details>

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

<details>
  <summary><em>English version</em></summary>
  <br>

```
src/ml/        Code-DKT and KCGen-KT, in PyTorch, independent of the app
src/api/       the FastAPI and SQLite API, organized by feature
src/web/       the React and TypeScript interface
tests/         regression tests, comparison with the paper and test data
experiments/   BKT and DKT under the same protocol as Code-DKT
docs/          architecture, decisions, method development and results
deploy/        the interface image
```

</details>

## Licença

A definir.
