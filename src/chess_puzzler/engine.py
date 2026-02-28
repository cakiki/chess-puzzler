import math
from chess.engine import SimpleEngine, Limit, Score

EVAL_LIMIT = Limit(depth=15, time=30, nodes=10_000_000)
PAIR_LIMIT = Limit(depth=50, time=30, nodes=30_000_000)
MATE_DEFENSE_LIMIT = Limit(depth=15, time=10, nodes=10_000_000)
MULTIPLIER = -0.00368208  # https://github.com/lichess-org/lila/pull/11148

def open_engine(path: str = "stockfish", threads: int = 4) -> SimpleEngine:
    engine = SimpleEngine.popen_uci(path)
    engine.configure({"Threads": threads})
    return engine

def win_chances(score: Score) -> float:
    mate = score.mate()
    if mate is not None:
        return 1 if mate > 0 else -1
    cp = score.score()
    if cp is None:
        return 0
    return 2 / (1 + math.exp(MULTIPLIER * cp)) - 1