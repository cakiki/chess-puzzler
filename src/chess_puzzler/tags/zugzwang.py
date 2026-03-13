from chess import Move
from chess.engine import SimpleEngine
from ..model import Puzzle
from ..engine import ZUGZWANG_LIMIT, win_chances


def zugzwang(engine: SimpleEngine, puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        board = node.board()
        if board.is_check():
            continue
        if len(list(board.legal_moves)) > 15:
            continue

        score = engine.analyse(board, limit=ZUGZWANG_LIMIT)["score"].pov(not puzzle.pov)

        rev_board = node.board()
        rev_board.push(Move.null())
        rev_score = engine.analyse(rev_board, limit=ZUGZWANG_LIMIT)["score"].pov(not puzzle.pov)

        if win_chances(score) < win_chances(rev_score) - 0.3:
            return True

    return False
