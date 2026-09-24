# Único bloqueio duro é a ausência de ambas as classes nos first-attempts; o resto é aviso.

from __future__ import annotations

import pandas as pd

from api.classroom_import.domain.value_objects.import_report import (
    AssignmentTrainability,
    ImportCheck,
)
from api.classroom_import.domain.services.submission_event import RUN_PROGRAM

# Espelha split_students_into_train_and_test; abaixo de 3 RP, aluno some da contagem, não bloqueia.
MIN_ATTEMPTS = 3

# Limiares de aviso são heurísticas, não número científico fixo; mudar aqui só muda o alerta.
SMALL_SAMPLE_THRESHOLD = 50  # [ASSUMED] amostra pequena abaixo disso (aviso brando)
TINY_SAMPLE_THRESHOLD = 20  # [ASSUMED] amostra muito pequena abaixo disso (aviso reforçado)

# <2 problemas distintos no assignment, sinal de cobertura rasa de KC; aviso, não bloqueio.
MIN_PROBLEMS = 2


def check_assignment_trainability(
    canonical_df: pd.DataFrame,
) -> tuple[list[AssignmentTrainability], list[ImportCheck]]:
    # both_classes_present é o único bloqueio duro; problemas/amostra só anexam avisos.
    summaries: list[AssignmentTrainability] = []
    checks: list[ImportCheck] = []

    for assignment_id, group in canonical_df.groupby("progsnap_assignment_id", sort=True):
        reasons: list[str] = []

        # Elegibilidade exige >=3 Run.Program; abaixo do piso, aluno não conta, mas não bloqueia.
        run = group[group["event_type"] == RUN_PROGRAM]
        attempts = run.groupby("student_id").size()
        eligible = attempts[attempts >= MIN_ATTEMPTS].index
        n_students_eligible = int(len(eligible))

        n_problems = int(group["problem_id"].nunique())
        n_submissions = int(len(group))

        # both_classes_present exige >=1 correct==1 e >=1 correct==0 no first-attempt de cada par.
        ordered = group.sort_values("submitted_at")
        first_attempts = ordered.drop_duplicates(subset=["student_id", "problem_id"], keep="first")
        classes = set(first_attempts["is_correct"].unique())
        both_classes_present = {0, 1}.issubset(classes)

        # trainable = both_classes_present, o único bloqueio duro; pisos abaixo só avisam.
        trainable = both_classes_present
        if not both_classes_present:
            reasons.append(
                "AUC indefinido: os first-attempts deste assignment têm uma única classe "
                "(todos acertaram ou todos erraram). Sem ambas as classes o Code-DKT não pode "
                "ser avaliado — o assignment fica só com as estatísticas pré-treino."
            )

        # Piso de problemas (<2), cobertura rasa de KC; aviso graduado, jamais parede.
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

        # Piso de amostra, poucos elegíveis, mais incerteza; aviso graduado, nunca bloqueio.
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
