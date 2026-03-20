from dataclasses import dataclass


@dataclass
class FinderConfig:
    win_chances_gap: float = 0.6
    attack_uniqueness_gap: float = 0.7
    min_advantage_cp: int = 200
    max_prev_score: int = 300
    min_clear_advantage: int = 400
    initial_score: int = 20
    mate_soon: int = 15


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
    win_chances_multiplier: float = -0.00368208  # https://github.com/lichess-org/lila/pull/11148

@dataclass
class MetricsConfig:
    counter_intuitive_threshold: float = 0.1
    max_depth: int = 30
    critical_depth_weight : float = 0.8
    capture_material_weight : float = 0.1