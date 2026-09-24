"""A checagem de treinabilidade de cada assignment: ready_for_kc_generation ou statistics_only.

O único veredito que torna o treino IMPOSSÍVEL, e portanto o único bloqueio, é a ausência de uma
das classes nas primeiras tentativas: sem ao menos um acerto E um erro, o first-attempt AUC é
matematicamente indefinido. Poucos problemas ou poucos alunos NÃO bloqueiam: são incerteza, não
impossibilidade, e viram avisos para o professor ler a mastery com cautela.

A checagem é por assignment: o A439 pode treinar e o A492 ficar só com estatísticas na mesma
turma. A elegibilidade do aluno espelha a divisão treino/teste do ml/ (3 ou mais Run.Program).

Módulo puro: sem I/O, sem SQL, sem ml/.
"""

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.value_objects.import_report import (
    AssignmentTrainability,
    ImportCheck,
)
from api.classroom_import.domain.services.submission_event import RUN_PROGRAM

# Espelha split_students_into_train_and_test (ml/code_dkt/student_split.py): só conta
# como elegível o aluno com >=3 eventos Run.Program. Alunos abaixo são EXCLUÍDOS da contagem,
# nunca bloqueiam o assignment.
MIN_ATTEMPTS = 3

# Limiares de AVISO (não de bloqueio). não há número
# científico fechado para "amostra pequena" — são heurísticas de cautela que disparam o aviso
# graduado, não a parede. Trocar aqui não muda quem treina, só a intensidade do alerta.
SMALL_SAMPLE_THRESHOLD = 50  # [ASSUMED] abaixo disso: amostra pequena (aviso brando)
TINY_SAMPLE_THRESHOLD = 20  # [ASSUMED] abaixo disso: amostra muito pequena (aviso reforçado)

# <2 problemas distintos no assignment: sinal de cobertura rasa de KC. Aviso, não bloqueio.
MIN_PROBLEMS = 2


def check_assignment_trainability(
    canonical_df: pd.DataFrame,
) -> tuple[list[AssignmentTrainability], list[ImportCheck]]:
    """Decide trainable vs statistics_only por-assignment sobre o dado limpo.

    Devolve (lista de AssignmentTrainability, lista de ImportCheck severity="viability"). O único
    bloqueio duro é both_classes_present=False; pisos de problemas/amostra só anexam avisos
    graduados e reasons, deixando `trainable` governado exclusivamente pela presença de classe.
    """
    summaries: list[AssignmentTrainability] = []
    checks: list[ImportCheck] = []

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

        # trainable = both_classes_present. É o ÚNICO bloqueio duro:
        # uma classe só => AUC matematicamente indefinido => statistics_only. Pisos abaixo só avisam.
        trainable = both_classes_present
        if not both_classes_present:
            reasons.append(
                "AUC indefinido: os first-attempts deste assignment têm uma única classe "
                "(todos acertaram ou todos erraram). Sem ambas as classes o Code-DKT não pode "
                "ser avaliado — o assignment fica só com as estatísticas pré-treino."
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
            checks.append(
                ImportCheck(
                    check="few_problems",
                    severity="viability",
                    message=msg,
                    count=n_problems,
                    location=f"AssignmentID={int(assignment_id)}",
                )
            )

        # Piso de amostra: poucos alunos elegíveis => mais incerteza na estimativa. AVISO graduado
        # (brando < 50, reforçado < 20), nunca bloqueio.
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
            checks.append(
                ImportCheck(
                    check="small_sample",
                    severity="viability",
                    message=msg,
                    count=n_students_eligible,
                    location=f"AssignmentID={int(assignment_id)}",
                )
            )

        summaries.append(
            AssignmentTrainability(
                progsnap_assignment_id=int(assignment_id),
                n_students_eligible=n_students_eligible,
                n_problems=n_problems,
                n_submissions=n_submissions,
                both_classes_present=both_classes_present,
                trainable=trainable,
                reasons=reasons,
            )
        )

    return summaries, checks
