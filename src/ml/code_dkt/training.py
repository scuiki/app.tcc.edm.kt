"""Treino do Code-DKT: Adam, gradient clipping e a loss do DKT, com os hiperparâmetros congelados."""

# Portado do TCC 1 (src/models/code_dkt.py). Numérica congelada. Duas parametrizações que não
# mexem nos números: o `device` e o callback `on_epoch` vêm de quem chama, com defaults que
# reproduzem o comportamento original.

from __future__ import annotations

from typing import Callable

import numpy as np
import torch
import torch.nn as nn

from ml.code_dkt.loss import dkt_loss
from ml.code_dkt.model import CodeDKTModel
from ml.code_dkt.model_input import build_model_input_tensors


def train_code_dkt(
    train_sequences: list[dict],
    problem_to_idx: dict[int, int],
    vocab: dict,
    config: dict,
    ast_paths_by_snapshot: dict[str, list],
    seed: int = 42,
    device: torch.device | None = None,
    on_epoch: Callable[[int, float], None] = lambda epoch, loss: None,
) -> CodeDKTModel:
    """Treina o CodeDKTModel com Adam e gradient clipping; chama `on_epoch(época, loss_média)`."""

    torch.manual_seed(seed)
    np.random.seed(seed)

    M = len(problem_to_idx)
    hidden_dim = config["hidden_dim"]
    dropout = config.get("dropout", 0.0)
    lr = config.get("lr", 0.0005)
    batch_size = config.get("batch_size", 128)
    epochs = config.get("epochs", 40)
    max_len = config.get("max_len", 50)
    R = config.get("R", 50)

    # device=None mantém o default original: cuda se houver, senão cpu.
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = CodeDKTModel(
        input_dim=2 * M,
        hidden_dim=hidden_dim,
        output_dim=M,
        node_count=vocab["node_count"],
        path_count=vocab["path_count"],
        n_layers=1,
        dropout=dropout,
        R=R,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    X, Y_next, mask = build_model_input_tensors(
        train_sequences, ast_paths_by_snapshot,
        vocab["token_to_idx"], vocab["path_to_idx"],
        problem_to_idx, max_len=max_len, R=R,
    )

    # y_true: correctness do próximo passo a_{t+1}
    correct_t = X[:, :, :M].sum(dim=-1)        # (N, max_len) — 1 se acerto no passo t
    y_true = torch.zeros_like(correct_t)
    y_true[:, :-1] = correct_t[:, 1:]          # shift: y_true[t] = correct[t+1]

    X = X.to(device)
    Y_next = Y_next.to(device)
    mask = mask.to(device)
    y_true = y_true.to(device)

    N = len(train_sequences)
    indices = np.arange(N)

    model.train()
    for epoch in range(1, epochs + 1):
        np.random.shuffle(indices)
        epoch_loss = 0.0
        n_batches = 0

        for start_i in range(0, N, batch_size):
            batch_idx = indices[start_i : start_i + batch_size]
            bt = torch.tensor(batch_idx, dtype=torch.long, device=device)

            y_pred = model(X[bt])
            loss = dkt_loss(y_pred, y_true[bt], Y_next[bt], mask[bt])

            optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
            optimizer.step()

            epoch_loss += loss.item()
            n_batches += 1

        avg_loss = epoch_loss / n_batches if n_batches > 0 else 0.0
        # O callback substitui o print por época do original (o default não faz nada).
        on_epoch(epoch, avg_loss)

    return model
