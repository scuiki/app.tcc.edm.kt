# Treino do Code-DKT, Adam + a loss por aluno do repositório, com o lote em pedaços na GPU.

# Adaptado do TCC 1 (src/models/code_dkt.py), com device e on_epoch injetáveis por quem chama.

from __future__ import annotations

from typing import Callable

import numpy as np
import torch

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
    # Treina o CodeDKTModel com Adam; chama `on_epoch(época, perda média por aluno)`.

    torch.manual_seed(seed)
    np.random.seed(seed)

    M = len(problem_to_idx)
    hidden_dim = config["hidden_dim"]
    lr = config.get("lr", 0.0005)
    batch_size = config.get("batch_size", 128)
    batch_chunk_size = config.get("batch_chunk_size", 64)
    epochs = config.get("epochs", 40)
    max_len = config.get("max_len", 50)
    R = config.get("R", 100)
    path_sampling_seed = config.get("path_sampling_seed", 42)

    # device=None mantém o default original, cuda se houver, senão cpu.
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = CodeDKTModel(
        input_dim=2 * M,
        hidden_dim=hidden_dim,
        output_dim=M,
        node_count=vocab["node_count"],
        path_count=vocab["path_count"],
        n_layers=1,
        R=R,
    ).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    X, Y_next, mask = build_model_input_tensors(
        train_sequences, ast_paths_by_snapshot,
        vocab["token_to_idx"], vocab["path_to_idx"],
        problem_to_idx, max_len=max_len, R=R, path_sampling_seed=path_sampling_seed,
    )

    # y_true é a correção do próximo passo, a_{t+1}
    correct_t = X[:, :, :M].sum(dim=-1)        # (N, max_len), 1 se acerto no passo t
    y_true = torch.zeros_like(correct_t)
    y_true[:, :-1] = correct_t[:, 1:]          # shift, y_true[t] = correct[t+1]

    # A perda da época é mostrada por aluno, contando só quem tem ao menos uma previsão válida
    n_students_in_loss = int((mask & (Y_next.sum(dim=-1) > 0)).any(dim=-1).sum())

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

        for start_i in range(0, N, batch_size):
            batch_idx = indices[start_i : start_i + batch_size]
            bt = torch.tensor(batch_idx, dtype=torch.long, device=device)

            # A perda soma a média de cada aluno, então a soma dos pedaços é a perda do lote inteiro
            optimizer.zero_grad()
            for chunk_i in range(0, len(batch_idx), batch_chunk_size):
                ct = bt[chunk_i : chunk_i + batch_chunk_size]
                loss = dkt_loss(model(X[ct]), y_true[ct], Y_next[ct], mask[ct])
                loss.backward()
                epoch_loss += loss.item()

            # Um passo do Adam por lote, depois de somar os pedaços, e sem corte de gradiente
            optimizer.step()

        loss_per_student = epoch_loss / n_students_in_loss if n_students_in_loss else 0.0
        # O callback substitui o print por época do original (o default não faz nada).
        on_epoch(epoch, loss_per_student)

    return model
