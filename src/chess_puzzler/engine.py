import math
from chess import Color
from chess.pgn import GameNode
from chess.engine import SimpleEngine, Limit, Score, Mate
from .model import EngineMove, NextMovePair

EVAL_LIMIT = Limit(depth=15, time=30, nodes=10_000_000)
PAIR_LIMIT = Limit(depth=50, time=30, nodes=30_000_000)
MATE_DEFENSE_LIMIT = Limit(depth=15, time=10, nodes=10_000_000)
MATE_SOON = Mate(15)
ZUGZWANG_LIMIT = Limit(depth=30, time=10, nodes=12_000_000)
MULTIPLIER = -0.00368208  # https://github.com/lichess-org/lila/pull/11148


def open_engine(path: str = "stockfish", threads: int = 4) -> SimpleEngine:
    """_summary_

    Args:
        path (str, optional): _description_. Defaults to "stockfish".
        threads (int, optional): _description_. Defaults to 4.

    Returns:
        SimpleEngine: _description_
    """
    engine = SimpleEngine.popen_uci(path)
    engine.configure({"Threads": threads})
    return engine


def win_chances(score: Score) -> float:
    """_summary_

    Args:
        score (Score): _description_

    Returns:
        float: _description_
    """
    mate = score.mate()
    if mate is not None:
        return 1 if mate > 0 else -1
    cp = score.score()
    if cp is None:
        return 0
    return 2 / (1 + math.exp(MULTIPLIER * cp)) - 1


def get_next_move_pair(engine: SimpleEngine, node: GameNode, winner: Color, limit: Limit) -> NextMovePair:
    """_summary_

    Args:
        engine (SimpleEngine): _description_
        node (GameNode): _description_
        winner (Color): _description_
        limit (Limit): _description_

    Returns:
        NextMovePair: _description_
    """
    info = engine.analyse(node.board(), multipv=2, limit=limit)
    best = EngineMove(info[0]["pv"][0], info[0]["score"].pov(winner))
    second = EngineMove(info[1]["pv"][0], info[1]["score"].pov(winner)) if len(info) > 1 else None
    return NextMovePair(node, winner, best, second)
