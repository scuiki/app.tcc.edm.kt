"""A loss do DKT (Piech et al., 2015, Eq. 3). Portado do TCC 1 (src/models/dkt.py); congelado."""

import torch
import torch.nn.functional as F
from torch import Tensor


def dkt_loss(
    y_pred: Tensor,
    y_true: Tensor,
    next_q: Tensor,
    mask: Tensor,
) -> Tensor:
    """Loss do DKT — Piech et al. (2015), Eq. 3.

    L = sum_t BCE(y_t^T * delta(q_{t+1}), a_{t+1})

    onde delta(q_{t+1}) é o one-hot do próximo problema e a_{t+1} é a
    correção da próxima tentativa. Apenas passos com mask=True E com
    próximo passo disponível contribuem para a loss.

    Args:
        y_pred: (N, max_len, M) — saída do DKTModel (após Sigmoid).
        y_true: (N, max_len) — correctness do próximo passo a_{t+1}.
        next_q: (N, max_len, M) — one-hot do próximo problema delta(q_{t+1}).
        mask: (N, max_len) — True onde há dado real (não padding).

    Returns:
        Scalar: loss média por evento válido não-mascarado.
    """
    # Piech et al. (2015) Eq. 3: y^T * delta(q_{t+1}) seleciona a predicao
    # para o proximo problema dentre as M saidas do LSTM
    pred_for_next = (y_pred * next_q).sum(dim=-1)  # (N, max_len)

    # Passos válidos: dado real E existe próximo problema (não é o último passo)
    valid = mask & (next_q.sum(dim=-1) > 0)

    if valid.sum() == 0:
        return torch.tensor(0.0, requires_grad=True, device=y_pred.device)

    loss = F.binary_cross_entropy(
        pred_for_next[valid],
        y_true[valid].float(),
        reduction="mean",
    )
    return loss
