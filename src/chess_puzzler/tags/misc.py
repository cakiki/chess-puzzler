from typing import List
import chess
from chess import (
    square_rank,
    square_file,
    square_distance,
    KING,
    QUEEN,
    KNIGHT,
    PAWN,
)

from ..model import Puzzle
from ..util import (
    moved_piece_type,
    is_capture,
    is_very_advanced_pawn_move,
    is_castling,
)


def en_passant(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if (
            moved_piece_type(node) == PAWN
            and square_file(node.move.from_square) != square_file(node.move.to_square)
            and not node.parent.board().piece_at(node.move.to_square)
        ):
            return True
    return False


def castling(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if is_castling(node):
            return True
    return False


def promotion(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if node.move.promotion:
            return True
    return False


def under_promotion(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if node.board().is_checkmate():
            return True if node.move.promotion == KNIGHT else False
        elif node.move.promotion and node.move.promotion != QUEEN:
            return True
    return False


def advanced_pawn(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if is_very_advanced_pawn_move(node):
            return True
    return False


def attacking_f2_f7(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        square = node.move.to_square
        if node.parent.board().piece_at(node.move.to_square) and square in [chess.F2, chess.F7]:
            king = node.board().piece_at(chess.E8 if square == chess.F7 else chess.E1)
            return king is not None and king.piece_type == KING and king.color != puzzle.pov
    return False


def kingside_attack(puzzle: Puzzle) -> bool:
    return side_attack(puzzle, 7, [6, 7], 20)


def queenside_attack(puzzle: Puzzle) -> bool:
    return side_attack(puzzle, 0, [0, 1, 2], 18)


def side_attack(puzzle: Puzzle, corner_file: int, king_files: List[int], nb_pieces: int) -> bool:
    back_rank = 7 if puzzle.pov else 0
    init_board = puzzle.mainline[0].board()
    king_square = init_board.king(not puzzle.pov)
    if (
        not king_square
        or square_rank(king_square) != back_rank
        or square_file(king_square) not in king_files
        or len(init_board.piece_map()) < nb_pieces  # no endgames
        or not any(node.board().is_check() for node in puzzle.mainline[1::2])
    ):
        return False
    score = 0
    corner = chess.square(corner_file, back_rank)
    for node in puzzle.mainline[1::2]:
        corner_dist = square_distance(corner, node.move.to_square)
        if node.board().is_check():
            score += 1
        if is_capture(node) and corner_dist <= 3:
            score += 1
        elif corner_dist >= 5:
            score -= 1
    return score >= 2
