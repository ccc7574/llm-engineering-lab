from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class TrainingConfig:
    data_path: str = "datasets/tiny_shakespeare/input.txt"
    out_dir: str = "runs/stage1_gpt"
    max_iters: int = 400
    eval_interval: int = 100
    eval_iters: int = 20
    batch_size: int = 32
    block_size: int = 64
    n_embed: int = 96
    n_head: int = 4
    n_layer: int = 4
    dropout: float = 0.1
    learning_rate: float = 3e-4
    seed: int = 1337
    device: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)
