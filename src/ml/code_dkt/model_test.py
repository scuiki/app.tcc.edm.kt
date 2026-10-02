# A rede do Code-DKT, com o W_0 do paper entre a atenção e o LSTM e sem dropout na saída do LSTM.

from __future__ import annotations

import inspect

import torch
import torch.nn as nn

from ml.code_dkt.model import CodeDKTModel

_M, _R = 2, 3


def _model() -> CodeDKTModel:
    torch.manual_seed(0)
    return CodeDKTModel(
        input_dim=2 * _M, hidden_dim=4, output_dim=_M, node_count=5, path_count=5,
        R=_R, node_embed_dim=6, path_embed_dim=6,
    ).eval()


def _input(path_index: int) -> torch.Tensor:
    # Duas execuções com o mesmo acerto e os mesmos problemas, mudando só o path de cada solução
    x = torch.zeros(1, 2, 2 * _M + 3 * _R)
    x[0, 0, 0] = x[0, 1, _M + 1] = 1.0
    x[0, :, 2 * _M :] = torch.tensor([2.0, float(path_index), 3.0] * _R)
    return x


def test_w0_is_square_and_without_bias():
    model = _model()
    full_dim = 2 * _M + 6 + 6 + 6
    assert model.code_vector_layer.weight.shape == (full_dim, full_dim)
    assert model.code_vector_layer.bias is None


def test_w0_is_created_after_the_attention_and_before_the_lstm():
    # A posição define a ordem dos números aleatórios que inicializam os pesos das camadas seguintes
    names = [name for name, _ in _model().named_children()]
    assert names.index("attention_layer") < names.index("code_vector_layer") < names.index("rnn")


def test_the_code_reaches_the_lstm_only_through_w0():
    model = _model()
    with torch.no_grad():
        assert not torch.equal(model(_input(2)), model(_input(4)))
        model.code_vector_layer.weight.zero_()
        assert torch.equal(model(_input(2)), model(_input(4)))


def test_the_lstm_output_has_no_dropout():
    model = _model()
    assert [m for m in model.modules() if isinstance(m, nn.Dropout)] == [model.embed_dropout]
    assert "dropout" not in inspect.signature(CodeDKTModel).parameters
