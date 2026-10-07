# csedm_problem_statements, a planilha oficial de enunciados da CSEDM

`problem_prompts_and_concepts.csv` é a planilha "2nd CSEDM Data Challenge - Problem Prompts &
Concepts Used", ligada pela página do dataset do desafio e baixada em 03/10/2026
(https://docs.google.com/spreadsheets/d/1-APxPAVP3PylM0fskzDNgpalj1DTuMqDLkgBC5QxJdg). Tem o
enunciado e as tags de conceito dos 50 problemas da CSEDM, e é igual à `data/prompt_concept.csv` do
repositório do Duan, que só acrescenta a coluna `Test Case Status`.

O teste de regressão do KCGen-KT a lê com o mesmo leitor da importação, para os prompts saírem
iguais aos da extração de referência.
