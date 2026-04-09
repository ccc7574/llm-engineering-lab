from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


@dataclass
class VerifierConfig:
    vocab_size: int
    block_size: int
    n_embed: int = 48
    hidden_dim: int = 64
    numeric_feature_dim: int = 6
    dropout: float = 0.1


class MiniVerifier(nn.Module):
    def __init__(self, config: VerifierConfig) -> None:
        super().__init__()
        self.config = config
        self.token_embedding = nn.Embedding(config.vocab_size, config.n_embed)
        self.position_embedding = nn.Embedding(config.block_size, config.n_embed)
        self.dropout = nn.Dropout(config.dropout)
        self.norm = nn.LayerNorm(config.n_embed)
        self.mlp = nn.Sequential(
            nn.Linear(config.n_embed + config.numeric_feature_dim, config.hidden_dim),
            nn.GELU(),
            nn.Dropout(config.dropout),
            nn.Linear(config.hidden_dim, 1),
        )

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        numeric_features: torch.Tensor | None = None,
    ) -> torch.Tensor:
        bsz, steps = input_ids.shape
        if steps > self.config.block_size:
            raise ValueError("sequence length exceeds verifier block size")
        positions = torch.arange(steps, device=input_ids.device)
        hidden = self.token_embedding(input_ids) + self.position_embedding(positions)[None, :, :]
        hidden = self.dropout(hidden)
        hidden = self.norm(hidden)

        mask = attention_mask.unsqueeze(-1).float()
        pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1.0)
        if numeric_features is None:
            numeric_features = torch.zeros(
                (bsz, self.config.numeric_feature_dim),
                dtype=pooled.dtype,
                device=pooled.device,
            )
        verifier_input = torch.cat([pooled, numeric_features], dim=-1)
        logits = self.mlp(verifier_input).squeeze(-1)
        return logits
