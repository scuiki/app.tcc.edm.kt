# Rede do Code-DKT (Shi et al. 2022), LSTM + atenção code2vec sobre AST paths; TCC 1, congelada.

from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor


class CodeDKTModel(nn.Module):
    # LSTM com atenção code2vec sobre os AST paths de cada tentativa.

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        node_count: int,
        path_count: int,
        n_layers: int = 1,
        dropout: float = 0.0,
        R: int = 50,
        node_embed_dim: int = 100,
        path_embed_dim: int = 100,
    ):

        super().__init__()
        self.input_dim = input_dim
        self.R = R
        embed_dim = node_embed_dim + path_embed_dim + node_embed_dim  # 300

        # +2 reserva slots para PAD (0) e UNK, c2vRNNModel.py linha 14
        self.embed_nodes = nn.Embedding(node_count + 2, node_embed_dim)
        self.embed_paths = nn.Embedding(path_count + 2, path_embed_dim)
        self.embed_dropout = nn.Dropout(0.2)  # ativo apenas em model.train()

        full_dim = input_dim + embed_dim  # 2M + 300 = 320

        # Seleção de path por atenção (score-attended), Shi et al. (2022), Seção 3
        self.path_transformation_layer = nn.Linear(full_dim, full_dim)
        # Softmax dim=2 (sobre R paths) segue o paper; o repo oficial usa dim=1 (sequência).
        self.attention_layer = nn.Linear(full_dim, 1)

        # LSTM, input = concat(x_t, code_vector) = 2M + (2M+300) = 340
        self.rnn = nn.LSTM(
            input_size=2 * input_dim + embed_dim,  # 2*2M+300=340 para M=10
            hidden_size=hidden_dim,
            num_layers=n_layers,
            batch_first=True,
        )
        self.dropout = nn.Dropout(p=dropout)
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: Tensor) -> Tensor:
        # (B, L, 2M + 3R) -> probabilidade de acerto por problema, (B, L, M).

        B, L, _ = x.shape

        # Separação do tensor combinado, c2vRNNModel.py linhas 39-42
        rnn_first_part = x[:, :, : self.input_dim]                   # (B, L, 2M)
        c2v_input = (
            x[:, :, self.input_dim :]
            .reshape(B, L, self.R, 3)
            .long()
        )                                                              # (B, L, R, 3)

        # Embeddings dos três componentes do path, c2vRNNModel.py linhas 48-50
        start_embed = self.embed_nodes(c2v_input[:, :, :, 0])        # (B, L, R, 100)
        path_embed = self.embed_paths(c2v_input[:, :, :, 1])         # (B, L, R, 100)
        end_embed = self.embed_nodes(c2v_input[:, :, :, 2])          # (B, L, R, 100)

        # x_t replicado para cada path, c2vRNNModel.py linha 40
        rnn_rep = rnn_first_part.unsqueeze(2).expand(-1, -1, self.R, -1)  # (B,L,R,2M)

        # full_embed é concat(start, end, path, x_t), c2vRNNModel.py linha 52
        full_embed = torch.cat(
            [start_embed, end_embed, path_embed, rnn_rep], dim=3
        )                                                              # (B, L, R, 2M+300)
        full_embed = self.embed_dropout(full_embed)                   # desligado em eval

        # Transformação + atenção, Shi et al. (2022), Seção 3
        transformed = torch.tanh(self.path_transformation_layer(full_embed))  # (B,L,R,320)
        attn_weights = torch.softmax(
            self.attention_layer(transformed), dim=2
        )                                                              # (B, L, R, 1)
        code_vectors = (full_embed * attn_weights).sum(dim=2)         # (B, L, 320)

        # Input do LSTM é concat(x_t, code_vector), Shi et al. (2022), Seção 3
        rnn_input = torch.cat([rnn_first_part, code_vectors], dim=2)  # (B, L, 340)

        out, _ = self.rnn(rnn_input)                                  # (B, L, hidden)
        out = self.dropout(out)
        return torch.sigmoid(self.fc(out))                            # (B, L, M)
