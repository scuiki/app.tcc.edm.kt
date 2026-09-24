"""Treinar e avaliar o Code-DKT num assignment: dado limpo entra, modelo e métricas saem.

A ordem das operações sustenta a reprodutibilidade e nunca é trocada:

    sequências completas → split → AST paths → vocabulário só do treino → índice de problemas
    (todos) → truncamento (só fatia) → treino → predição → AUCs separadas

O teste de regressão contra o TCC 1 é o oráculo que reprova qualquer troca.
"""

from __future__ import annotations

from typing import Callable, Mapping

import pandas as pd
import torch

from ml.code_dkt.ast_paths import extract_ast_paths_for_snapshots
from ml.code_dkt.prediction import predict_code_dkt
from ml.code_dkt.problem_index import build_problem_index
from ml.code_dkt.student_sequences import build_student_sequences, truncate_student_sequences
from ml.code_dkt.student_split import (
    build_train_only_vocabulary,
    split_students_into_train_and_test,
)
from ml.code_dkt.training import train_code_dkt
from ml.evaluation.auc import compute_auc


def code_by_snapshot_id(df: pd.DataFrame) -> dict[str, str]:
    """snapshot id -> código Java. Um snapshot tem um código só; a última linha vence."""
    return dict(zip(df["code_snapshot_id"].astype(str), df["code"].fillna("")))


def code_snapshot_ids(sequences: list[dict]) -> list[str]:
    """Todos os snapshot ids dos eventos das sequências, em ordem (com repetições)."""
    out: list[str] = []
    for seq in sequences:
        out.extend(seq["events"]["code_snapshot_id"].astype(str).tolist())
    return out


def train_and_evaluate(
    df_or_train: pd.DataFrame,
    config: Mapping,
    test_df: pd.DataFrame | None = None,
    *,
    progsnap_assignment_id: int,
    device: torch.device | None = None,
    on_epoch: Callable[[int, float], None] = lambda epoch, loss: None,
    n_workers: int | None = 1,
) -> dict:
    """Treina e avalia o Code-DKT em um assignment.

    Aceita UM DataFrame (dividido aqui por split_students_into_train_and_test, com o
    random_state=1 do TCC 1) OU o par treino/teste já dividido. Nos dois casos a ordem das
    operações é a mesma e o vocabulário sai só do treino.

    Devolve {model, config, vocab, first_attempt_auc, all_attempts_auc, predictions,
    n_train_events, n_test_events}. A semente é responsabilidade de quem chama
    (seed_all_random_generators), antes desta função.
    """
    if test_df is None:
        train_df, test_df = split_students_into_train_and_test(df_or_train)
    else:
        train_df = df_or_train

    max_len = config.get("max_len", 50)
    R = config.get("R", 50)

    # 1. sequências completas: is_first_attempt é marcado uma vez por partição
    train_sequences = build_student_sequences(train_df, progsnap_assignment_id)
    test_sequences = build_student_sequences(test_df, progsnap_assignment_id)

    # 2. AST paths de todos os snapshots, treino e teste
    code_by_snapshot = code_by_snapshot_id(pd.concat([train_df, test_df], ignore_index=True))
    all_snapshot_ids = sorted(
        set(code_snapshot_ids(train_sequences)) | set(code_snapshot_ids(test_sequences))
    )
    ast_paths_by_snapshot = extract_ast_paths_for_snapshots(
        all_snapshot_ids, code_by_snapshot,
        max_path_length=config.get("max_path_length", 8),
        max_path_width=config.get("max_path_width", 2),
        R=R, seed=config.get("seed", 42), n_workers=n_workers,
    )

    # 3. vocabulário só do treino: sem vazamento por construção
    token_to_idx, path_to_idx = build_train_only_vocabulary(
        ast_paths_by_snapshot, code_snapshot_ids(train_sequences)
    )
    vocab = {
        "token_to_idx": token_to_idx,
        "path_to_idx": path_to_idx,
        "node_count": len(token_to_idx),
        "path_count": len(path_to_idx),
    }

    # 4. índice de problemas sobre TODAS as sequências (a saída do modelo cobre todo problema)
    problem_to_idx = build_problem_index(train_sequences + test_sequences)

    # 5. truncamento: só fatia, is_first_attempt segue como foi marcado
    train_sequences = truncate_student_sequences(train_sequences, max_len=max_len)
    test_sequences = truncate_student_sequences(test_sequences, max_len=max_len)

    # 6. treino + predição (device e on_epoch vêm de quem chama)
    model = train_code_dkt(
        train_sequences, problem_to_idx, vocab, dict(config), ast_paths_by_snapshot,
        seed=config.get("seed", 42), device=device, on_epoch=on_epoch,
    )
    predictions = predict_code_dkt(
        model, test_sequences, problem_to_idx, vocab, ast_paths_by_snapshot,
        max_len=max_len, R=R,
    )

    n_train_events = sum(min(len(s["events"]), max_len) for s in train_sequences)

    # 7. métricas separadas: a mesma compute_auc, só a flag muda
    return {
        "model": model,
        "config": config,
        "vocab": vocab,
        "first_attempt_auc": compute_auc(predictions, first_attempt_only=True),
        "all_attempts_auc": compute_auc(predictions, first_attempt_only=False),
        "predictions": predictions,
        "n_train_events": n_train_events,
        "n_test_events": len(predictions),
    }
