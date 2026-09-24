# A loss do DKT (Piech et al., 2015, Eq. 3). Portado do TCC 1 (src/models/dkt.py), congelado.

import torch
import torch.nn.functional as F
from torch import Tensor


def dkt_loss(
    y_pred: Tensor,  # (N, max_len, M), saída do DKTModel após Sigmoid
    y_true: Tensor,  # (N, max_len), correção do próximo passo a_{t+1}
    next_q: Tensor,  # (N, max_len, M), one-hot do próximo problema delta(q_{t+1})
    mask: Tensor,  # (N, max_len), True onde há dado real, sem padding
) -> Tensor:
    # Eq. 3 de Piech et al. (2015), y^T * delta(q_{t+1}) seleciona a predição do próximo problema.
    pred_for_next = (y_pred * next_q).sum(dim=-1)  # (N, max_len)

    # Passos válidos, tem dado real e existe próximo problema (não é o último passo).
    valid = mask & (next_q.sum(dim=-1) > 0)

    if valid.sum() == 0:
        return torch.tensor(0.0, requires_grad=True, device=y_pred.device)

    loss = F.binary_cross_entropy(
        pred_for_next[valid],
        y_true[valid].float(),
        reduction="mean",
    )
    return loss  # média por evento válido não mascarado
