# EDM·KT

Ferramenta web para o professor de programação introdutória ver, durante a disciplina, quais
conceitos a turma ainda não domina. O professor importa os envios de código da turma no formato
ProgSnap2, o app extrai os conceitos (*knowledge components*) de cada exercício com o KCGen-KT
(Duan et al., 2026), o professor revisa esses conceitos, e o app treina o Code-DKT (Shi et al., 2022)
sobre os dados da própria turma para estimar o domínio de cada aluno em cada conceito.

> **English.** EDM·KT is a web tool that shows introductory programming instructors, during the
> course, which concepts their class has not mastered yet. It extracts knowledge components from
> students' Java submissions (ProgSnap2) with KCGen-KT and trains a Code-DKT knowledge tracing
> model on the class's own data.

## Publicações

- **Monografia.** VIANA, E. M.; OLIVEIRA, L. K.; BORBA, V. S. *Análise do aprendizado de
  programação utilizando mineração de dados educacionais*. Trabalho de Conclusão de Curso
  (Engenharia de Computação), UniFacens, Coordenadoria de Engenharia da Computação, Sorocaba, 2026.
  103 f. Orientadora: Profa. Ma. Talita dos Reis Lopes Berbel.
- **Resumo expandido.** OLIVEIRA, L. K.; VIANA, E. M.; BORBA, V. S.; BERBEL, T. R. L.
  *Identificação de padrões de aprendizagem em programação por meio da análise de códigos de
  estudantes e da mineração de dados educacionais*. I Congresso Nacional de Inovação em Educação,
  Ciência e Tecnologia (CONAIDUC), on-line, 6 a 9 de julho de 2026. ISBN 9786588884621.
  DOI [10.51189/conaiduc/83301](https://doi.org/10.51189/conaiduc/83301).

O resumo expandido apresenta a modelagem e propõe, como trabalho futuro, uma ferramenta de apoio ao
professor. Este repositório é essa ferramenta. Para citar, use o botão *Cite this repository*.

<p>
  <img src="docs/assets/unifacens.png" alt="UniFacens" height="28">
  &nbsp;&nbsp;
  <img src="docs/assets/conaiduc.png" alt="CONAIDUC" height="40">
</p>

## Requisitos

- **Docker com o Compose.** As imagens ocupam cerca de 15 GB, e a do app é `amd64` (x86-64).
- **Credencial do Claude.** A geração dos conceitos usa o Claude Haiku 4.5 pelo CLI `claude`, que
  já vem na imagem. Serve o token de uma assinatura do Claude (`claude setup-token`) ou uma chave da
  API da Anthropic. Sem ela, o exercício não chega ao treino.
- **GPU NVIDIA, opcional.** Com o [NVIDIA Container
  Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html),
  o treino usa a GPU. Sem ela, roda na CPU, mais devagar.

## Como rodar

```bash
git clone https://github.com/scuiki/app.tcc.edm.kt.git
cd app.tcc.edm.kt
cp .env.example .env
```

No `.env`, preencha a credencial do Claude e, se tiver GPU, descomente o `COMPOSE_FILE`. Depois

```bash
docker compose up -d --build
```

O primeiro build baixa a imagem do PyTorch, as dependências e os modelos de vetores, e leva alguns
minutos. O app abre em <http://127.0.0.1:5173>, só nesta máquina. Para abrir de outra, veja o
`EDMKT_BIND_IP` no `.env.example`.

No app, crie uma turma, importe um `.zip` ProgSnap2 com o `MainTable.csv` e o `CodeStates.csv`, gere
e revise os conceitos de cada exercício, treine o modelo e abra a análise.

Os testes de regressão e os resultados em `docs/results` usam a CSEDM, variante CodeWorkout de
Spring 2019, do 2nd CSEDM Data Challenge, que não vem no repositório. Ela está no
[PSLC DataShop](https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=3458), com cadastro
gratuito, e serve também para experimentar o app.

Os dados da turma ficam em `data/` e no `app.db`, na pasta do repositório. Para parar, use
`docker compose down`.

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

Os testes unitários ficam ao lado do código que testam. Para ir além, veja o
[`ARCHITECTURE.md`](docs/ARCHITECTURE.md), o [`DEVELOPMENT.md`](docs/DEVELOPMENT.md), com a
fidelidade aos dois métodos, os testes e a reprodução, e o [`DECISIONS.md`](docs/DECISIONS.md).

## Licença

A definir.
