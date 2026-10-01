# A loss do Code-DKT, a média dos erros de cada aluno somada no lote, como o repositório oficial.

import torch
import torch.nn.functional as F
from torch import Tensor


def dkt_loss(
    y_pred: Tensor,  # (N, max_len, M), saída do modelo após Sigmoid
    y_true: Tensor,  # (N, max_len), correção do próximo passo a_{t+1}
    next_q: Tensor,  # (N, max_len, M), one-hot do próximo problema delta(q_{t+1})
    mask: Tensor,  # (N, max_len), True onde há dado real, sem padding
) -> Tensor:
    # y^T * delta(q_{t+1}) seleciona a previsão do próximo problema (Piech et al., 2015, Eq. 3)
    pred_for_next = (y_pred * next_q).sum(dim=-1)  # (N, max_len)

    # Passos válidos, tem dado real e existe próximo problema, então a 1ª execução nunca é alvo
    valid = mask & (next_q.sum(dim=-1) > 0)

    # Só operações densas, sem índice nem soma espalhada, que perderiam a repetição na GPU
    safe_pred = torch.where(valid, pred_for_next, torch.full_like(pred_for_next, 0.5))
    step_loss = F.binary_cross_entropy(safe_pred, y_true.float(), reduction="none")
    step_loss = torch.where(valid, step_loss, torch.zeros_like(step_loss))

    # O aluno sem previsão válida soma zero, sem dividir por zero
    n_valid = valid.sum(dim=-1)
    per_student = step_loss.sum(dim=-1) / n_valid.clamp(min=1)
    return per_student.sum()
