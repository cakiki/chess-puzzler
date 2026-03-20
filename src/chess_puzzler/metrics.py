from chess import Board
import chess
from chess.engine import SimpleEngine, Limit

from chess_puzzler.util import piece_value
from .model import Puzzle


def critical_depth(engine: SimpleEngine, puzzle: Puzzle, max_depth: int = 30) -> int | None:
    """critical depth from "Generating Creative Chess Puzzles" https://openreview.net/forum?id=TNZse5q2Tr

    Args:
        engine (SimpleEngine): _description_
        puzzle (Puzzle): _description_
        max_depth (int, optional): _description_. Defaults to 30.

    Returns:
        int | None: _description_
    """
    board = Board(puzzle.fen)
    board.push(puzzle.moves[0])
    solution_move = puzzle.moves[1]
    for depth in range(1, max_depth + 1):
        info = engine.analyse(board, Limit(depth=depth))
        pv = info.get("pv")
        if pv and pv[0] == solution_move:
            return depth
    return None


def counter_intuitiveness(engine, puzzle, max_depth=30, cd=None):
    """counter intuitiveness from "Generating Creative Chess Puzzles" https://openreview.net/forum?id=TNZse5q2Tr

    Args:
        engine (_type_): _description_
        puzzle (_type_): _description_
        max_depth (int, optional): _description_. Defaults to 30.
        cd (_type_, optional): _description_. Defaults to None.

    Returns:
        _type_: _description_
    """
    if cd is None:
        cd = critical_depth(engine, puzzle, max_depth)
    if cd is None:
        return 1.0
    board = chess.Board(puzzle.fen)
    board.push(puzzle.moves[0])
    captured = board.piece_at(puzzle.moves[1].to_square)
    capture_value = piece_value(captured.piece_type) / 9 if captured else 0
    return 0.8 * (cd / max_depth) + 0.1 * (-capture_value)
