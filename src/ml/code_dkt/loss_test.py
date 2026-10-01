# A perda do Code-DKT, a média de cada aluno somada no lote, sem a primeira execução como alvo.

from __future__ import annotations

import torch
import torch.nn.functional as F

from ml.code_dkt.loss import dkt_loss


def _batch(students: list[list[tuple[int, int]]], max_len: int = 6, M: int = 2):
    # Cada aluno é a lista de (problema, acerto) das execuções, à direita como na entrada do modelo
    N = len(students)
    y_pred = torch.full((N, max_len, M), 0.5)
    y_true = torch.zeros(N, max_len)
    next_q = torch.zeros(N, max_len, M)
    mask = torch.zeros(N, max_len, dtype=torch.bool)
    for i, runs in enumerate(students):
        pad = max_len - len(runs)
        for t_rel, _run in enumerate(runs):
            mask[i, pad + t_rel] = True
            if t_rel + 1 < len(runs):
                next_problem, next_correct = runs[t_rel + 1]
                next_q[i, pad + t_rel, next_problem] = 1.0
                y_true[i, pad + t_rel] = next_correct
    return y_pred, y_true, next_q, mask


def test_the_first_run_is_never_a_target():
    y_pred, y_true, next_q, mask = _batch([[(0, 1), (1, 0), (0, 1)]])
    y_pred[0, 3, 1], y_pred[0, 4, 0] = 0.3, 0.8
    expected = (
        F.binary_cross_entropy(torch.tensor(0.3), torch.tensor(0.0))
        + F.binary_cross_entropy(torch.tensor(0.8), torch.tensor(1.0))
    ) / 2
    torch.testing.assert_close(dkt_loss(y_pred, y_true, next_q, mask), expected)

    # O repositório preveria a primeira execução a partir da posição vazia antes dela, e aqui não
    repo_q, repo_true, repo_pred = next_q.clone(), y_true.clone(), y_pred.clone()
    repo_q[0, 2, 0], repo_true[0, 2], repo_pred[0, 2, 0] = 1.0, 1.0, 0.01
    torch.testing.assert_close(dkt_loss(repo_pred, repo_true, repo_q, mask), expected)


def test_a_student_with_one_run_adds_nothing_and_gives_no_nan():
    y_pred, y_true, next_q, mask = _batch([[(0, 1)], [(0, 0), (1, 1)]])
    y_pred.requires_grad_(True)
    loss = dkt_loss(y_pred, y_true, next_q, mask)
    loss.backward()

    torch.testing.assert_close(loss, dkt_loss(*_batch([[(0, 0), (1, 1)]])))
    assert torch.isfinite(y_pred.grad).all()

    # Um lote só com alunos de uma execução dá perda zero, ainda sem NaN
    only = _batch([[(0, 1)], [(1, 0)]])
    only[0].requires_grad_(True)
    empty = dkt_loss(*only)
    empty.backward()
    assert empty.item() == 0.0 and torch.isfinite(only[0].grad).all()


def test_the_batch_sums_the_mean_of_each_student():
    students = [[(0, 1), (1, 0), (0, 1)], [(1, 1), (0, 0), (1, 1), (0, 0), (1, 1)]]
    y_pred, y_true, next_q, mask = _batch(students)
    y_pred = torch.rand(y_pred.shape, generator=torch.Generator().manual_seed(3)) * 0.9 + 0.05

    per_student = []
    for i, runs in enumerate(students):
        pad = 6 - len(runs)
        losses = [
            F.binary_cross_entropy(
                y_pred[i, pad + t, runs[t + 1][0]], torch.tensor(float(runs[t + 1][1]))
            )
            for t in range(len(runs) - 1)
        ]
        per_student.append(torch.stack(losses).mean())

    torch.testing.assert_close(dkt_loss(y_pred, y_true, next_q, mask), sum(per_student))
