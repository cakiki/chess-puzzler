import chess
from chess import PAWN
from chess.pgn import ChildNode


from ..model import Puzzle
from ..util import (
    material_diff,
    VALUES,

    is_hanging,

    is_trapped,
)

def sacrifice(puzzle: Puzzle) -> bool:
    # down in material compared to initial position, after moving
    diffs = [material_diff(n.board(), puzzle.pov) for n in puzzle.mainline]
    initial = diffs[0]
    for d in diffs[1::2][1:]:
        if d - initial <= -2:
            return not any(n.move.promotion for n in puzzle.mainline[::2][1:])
    return False

def hanging_piece(puzzle: Puzzle) -> bool:
    to = puzzle.mainline[1].move.to_square
    captured = puzzle.mainline[0].board().piece_at(to)
    if puzzle.mainline[0].board().is_check() and (not captured or captured.piece_type == PAWN):
        return False
    if captured and captured.piece_type != PAWN:
        if is_hanging(puzzle.mainline[0].board(), captured, to):
            op_move = puzzle.mainline[0].move
            op_capture = chess.Board(puzzle.fen).piece_at(op_move.to_square)
            if op_capture and VALUES[op_capture.piece_type] >= VALUES[captured.piece_type] and op_move.to_square == to:
                return False
            if len(puzzle.mainline) < 4:
                return True
            if material_diff(puzzle.mainline[3].board(), puzzle.pov) >= material_diff(
                puzzle.mainline[1].board(), puzzle.pov
            ):
                return True
    return False


def trapped_piece(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        square = node.move.to_square
        captured = node.parent.board().piece_at(square)
        if captured and captured.piece_type != PAWN:
            prev = node.parent
            assert isinstance(prev, ChildNode)
            if prev.move.to_square == square:
                square = prev.move.from_square
            if is_trapped(prev.parent.board(), square):
                return True
    return False
