from chess import (
    Board,
    PieceType,
    KING,
    QUEEN,
    ROOK,
    PAWN,
    WHITE,
    BLACK,
)

from ..model import Puzzle


def piece_endgame(puzzle: Puzzle, piece_type: PieceType) -> bool:
    """_summary_

    Args:
        puzzle (Puzzle): _description_
        piece_type (PieceType): _description_

    Returns:
        bool: _description_
    """
    for board in [puzzle.mainline[i].board() for i in [0, 1]]:
        if not board.pieces(piece_type, WHITE) and not board.pieces(piece_type, BLACK):
            return False
        for piece in board.piece_map().values():
            if not piece.piece_type in [KING, PAWN, piece_type]:
                return False
    return True


def queen_rook_endgame(puzzle: Puzzle) -> bool:
    """_summary_

    Args:
        puzzle (Puzzle): _description_

    Returns:
        bool: _description_
    """
    def test(board: Board) -> bool:
        pieces = board.piece_map().values()
        return (
            len([p for p in pieces if p.piece_type == QUEEN]) == 1
            and any(p.piece_type == ROOK for p in pieces)
            and all(p.piece_type in [QUEEN, ROOK, PAWN, KING] for p in pieces)
        )

    return all(test(puzzle.mainline[i].board()) for i in [0, 1])
