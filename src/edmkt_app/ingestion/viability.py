"""Estágio D da ingestão: o gate de viabilidade por-assignment (INGEST-03 / D-08 / D-09 RESOLVIDO).

INGEST-03 é o "gate é a feature" do projeto, mas na versão RESOLVIDA do D-09 ele combate o
comportamento silencioso SEM cair em pisos mágicos. O único veredito que torna o treino
genuinamente impossível — e portanto o único bloqueio duro (trainable=False / EDA-only) — é a
ausência de ambas as classes nos first-attempts de um assignment: sem ≥1 acerto E ≥1 erro,
`roc_auc_score` levanta "Only one class present" e a métrica primária (first-attempt AUC) fica
matematicamente indefinida.

Pisos de problemas e de tamanho de amostra NÃO bloqueiam: são incerteza, não impossibilidade. A
mitigação real (intervalos de confiança, cautela na leitura) é da Fase 6 — aqui eles viram avisos
graduados acionáveis (severity="viability"), nunca uma parede que esconde dado computável.

O gate é por-assignment (D-08): A439 pode ser trainable e A492 EDA-only na mesma turma. A
elegibilidade de aluno espelha o `split_students_into_train_and_test` do núcleo (min_attempts≥3 Run.Program).

Módulo puro (DataFrame-in → contrato-out): sem I/O, sem SQL, sem import de ml.
"""

from __future__ import annotations

import pandas as pd

from edmkt_app.ingestion.report import AssignmentSummary, ReportItem
from edmkt_app.submission_events import RUN_PROGRAM

# Espelha split_students_into_train_and_test (../tcc.edm.kt data_loader → ml/code_dkt/student_split.py:41-44): só conta
# como elegível o aluno com >=3 eventos Run.Program. Alunos abaixo são EXCLUÍDOS da contagem,
# nunca bloqueiam o assignment.
MIN_ATTEMPTS = 3

# Limiares de AVISO (não de bloqueio). [ASSUMED] no RESEARCH (~50 / ~20): não há número
# científico fechado para "amostra pequena" — são heurísticas de cautela que disparam o aviso
# graduado, não a parede. Trocar aqui não muda quem treina, só a intensidade do alerta.
SMALL_SAMPLE_THRESHOLD = 50  # [ASSUMED] abaixo disso: amostra pequena (aviso brando)
TINY_SAMPLE_THRESHOLD = 20  # [ASSUMED] abaixo disso: amostra muito pequena (aviso reforçado)

# <2 problemas distintos no assignment: sinal de cobertura rasa de KC. Aviso, não bloqueio.
MIN_PROBLEMS = 2


def assess_viability(
    canonical_df: pd.DataFrame,
) -> tuple[list[AssignmentSummary], list[ReportItem]]:
    """Decide trainable vs EDA-only por-assignment sobre o stream canônico (D-08/D-09).

    Devolve (lista de AssignmentSummary, lista de ReportItem severity="viability"). O único
    bloqueio duro é both_classes_present=False; pisos de problemas/amostra só anexam avisos
    graduados e reasons, deixando `trainable` governado exclusivamente pela presença de classe.
    """
    summaries: list[AssignmentSummary] = []
    items: list[ReportItem] = []

    for assignment_id, group in canonical_df.groupby("progsnap_assignment_id", sort=True):
        reasons: list[str] = []

        # Elegibilidade min_attempts>=3 Run.Program por aluno (espelha o núcleo): alunos abaixo
        # do piso não contam como elegíveis, mas a sua presença não derruba o assignment.
        run = group[group["event_type"] == RUN_PROGRAM]
        attempts = run.groupby("student_id").size()
        eligible = attempts[attempts >= MIN_ATTEMPTS].index
        n_students_eligible = int(len(eligible))

        n_problems = int(group["problem_id"].nunique())
        n_submissions = int(len(group))

        # both_classes_present: nos first-attempts (primeira ocorrência temporal de cada par
        # SubjectID×ProblemID) precisa haver ≥1 correct==1 E ≥1 correct==0 — sem isso o AUC é
        # indefinido. Ordena por ServerTimestamp e pega a 1ª linha de cada par.
        ordered = group.sort_values("submitted_at")
        first_attempts = ordered.drop_duplicates(subset=["student_id", "problem_id"], keep="first")
        classes = set(first_attempts["is_correct"].unique())
        both_classes_present = {0, 1}.issubset(classes)

        # trainable = both_classes_present — A POLÍTICA RESOLVIDA (D-09). É o ÚNICO bloqueio duro:
        # uma classe só => AUC matematicamente indefinido => EDA-only. Pisos abaixo só avisam.
        trainable = both_classes_present
        if not both_classes_present:
            reasons.append(
                "AUC indefinido: os first-attempts deste assignment têm uma única classe "
                "(todos acertaram ou todos erraram). Sem ambas as classes o Code-DKT não pode "
                "ser avaliado — assignment marcado como EDA-only."
            )

        # Piso de problemas (<2): cobertura rasa de KC. AVISO graduado, jamais parede — trainable
        # já está decidido só pela classe acima.
        if n_problems < MIN_PROBLEMS:
            msg = (
                f"Apenas {n_problems} problema(s) distinto(s) neste assignment: a cobertura de "
                "Knowledge Components fica rasa. O treino segue possível, mas leia a mastery com "
                "cautela."
            )
            reasons.append(msg)
            items.append(
                ReportItem(
                    check="few_problems",
                    severity="viability",
                    message=msg,
                    count=n_problems,
                    location=f"AssignmentID={int(assignment_id)}",
                )
            )

        # Piso de amostra: poucos alunos elegíveis => mais incerteza na estimativa. AVISO graduado
        # (brando < 50, reforçado < 20), nunca bloqueio (mitigação real é Fase 6).
        if n_students_eligible < SMALL_SAMPLE_THRESHOLD:
            reforcado = n_students_eligible < TINY_SAMPLE_THRESHOLD
            msg = (
                f"Apenas {n_students_eligible} aluno(s) elegível(is) (≥{MIN_ATTEMPTS} execuções): "
                + (
                    "amostra muito pequena — as estimativas de mastery terão alta incerteza."
                    if reforcado
                    else "amostra pequena — interprete a mastery com cautela."
                )
            )
            reasons.append(msg)
            items.append(
                ReportItem(
                    check="small_sample",
                    severity="viability",
                    message=msg,
                    count=n_students_eligible,
                    location=f"AssignmentID={int(assignment_id)}",
                )
            )

        summaries.append(
            AssignmentSummary(
                assignment_id=int(assignment_id),
                n_students_eligible=n_students_eligible,
                n_problems=n_problems,
                n_submissions=n_submissions,
                both_classes_present=both_classes_present,
                trainable=trainable,
                reasons=reasons,
            )
        )

    return summaries, items
