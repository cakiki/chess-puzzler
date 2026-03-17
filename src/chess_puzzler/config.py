from dataclasses import dataclass

from chess.engine import Limit, Mate


@dataclass
class FinderConfig:
    win_chances_gap: float = 0.6
    attack_uniqueness_gap: float = 0.7
    min_advantage_cp: int = 200
    max_prev_score: int = 300
    min_clear_advantage: int = 400
    initial_score: int = 20

@dataclass
class EngineConfig:
    eval_depth: int = 15
    eval_time: int = 30
    eval_nodes: int = 10_000_000
    pair_depth: int = 50
    pair_time: int = 30
    pair_nodes: int = 30_000_000
    mate_defense_depth: int = 15
    mate_defense_time: int = 10
    mate_defense_nodes: int = 10_000_000
    zugzwang_depth: int = 30
    zugzwang_time: int = 10
    zugzwang_nodes: int = 12_000_000

EVAL_LIMIT = Limit(depth=15, time=30, nodes=10_000_000)
PAIR_LIMIT = Limit(depth=50, time=30, nodes=30_000_000)
MATE_DEFENSE_LIMIT = Limit(depth=15, time=10, nodes=10_000_000)
MATE_SOON = Mate(15)
ZUGZWANG_LIMIT = Limit(depth=30, time=10, nodes=12_000_000)
MULTIPLIER = -0.00368208  # https://github.com/lichess-org/lila/pull/11148
