from typing import Optional
import chess
from chess import (
    square_rank,
    square_file,
    SquareSet,
    square_distance,
    QUEEN,
    ROOK,
    BISHOP,
    KNIGHT,
    PAWN,
)
from chess.pgn import ChildNode
from ..model import Puzzle
from ..util import (
    moved_piece_type,
    attacker_pieces,
)

def smothered_mate(puzzle: Puzzle) -> bool:
    board = puzzle.mainline[-1].board()
    king_square = board.king(not puzzle.pov)
    assert king_square is not None
    for checker_square in board.checkers():
        piece = board.piece_at(checker_square)
        assert piece
        if piece.piece_type == KNIGHT:
            for escape_square in [s for s in chess.SQUARES if square_distance(s, king_square) == 1]:
                blocker = board.piece_at(escape_square)
                if not blocker or blocker.color == puzzle.pov:
                    return False
            return True
    return False


def mate_in(puzzle: Puzzle) -> Optional[str]:
    if not puzzle.mainline[-1].board().is_checkmate():
        return None
    moves_to_mate = len(puzzle.mainline) // 2
    if moves_to_mate == 1:
        return "mateIn1"
    elif moves_to_mate == 2:
        return "mateIn2"
    elif moves_to_mate == 3:
        return "mateIn3"
    elif moves_to_mate == 4:
        return "mateIn4"
    return "mateIn5"

def dovetail_mate(puzzle: Puzzle) -> bool:
    node = puzzle.mainline[-1]
    board = node.board()
    king = board.king(not puzzle.pov)
    assert king is not None
    assert isinstance(node, ChildNode)
    if square_file(king) in [0, 7] or square_rank(king) in [0, 7]:
        return False
    queen_square = node.move.to_square
    if (
        moved_piece_type(node) != QUEEN
        or square_file(queen_square) == square_file(king)
        or square_rank(queen_square) == square_rank(king)
        or square_distance(queen_square, king) > 1
    ):
        return False
    for square in [s for s in SquareSet(chess.BB_ALL) if square_distance(s, king) == 1]:
        if square == queen_square:
            continue
        attackers = list(board.attackers(puzzle.pov, square))
        if attackers == [queen_square]:
            if board.piece_at(square):
                return False
        elif attackers:
            return False
    return True

def boden_or_double_bishop_mate(puzzle: Puzzle) -> Optional[str]:
    node = puzzle.mainline[-1]
    board = node.board()
    king = board.king(not puzzle.pov)
    assert king is not None
    assert isinstance(node, ChildNode)
    bishop_squares = list(board.pieces(BISHOP, puzzle.pov))
    if len(bishop_squares) < 2:
        return None
    for square in [s for s in SquareSet(chess.BB_ALL) if square_distance(s, king) < 2]:
        if not all([p.piece_type == BISHOP for p in attacker_pieces(board, puzzle.pov, square)]):
            return None
    if (square_file(bishop_squares[0]) < square_file(king)) == (square_file(bishop_squares[1]) > square_file(king)):
        return "bodenMate"
    else:
        return "doubleBishopMate"
    

def arabian_mate(puzzle: Puzzle) -> bool:
    node = puzzle.mainline[-1]
    board = node.board()
    king = board.king(not puzzle.pov)
    assert king is not None
    assert isinstance(node, ChildNode)
    if (
        square_file(king) in [0, 7]
        and square_rank(king) in [0, 7]
        and moved_piece_type(node) == ROOK
        and square_distance(node.move.to_square, king) == 1
    ):
        for knight_square in board.attackers(puzzle.pov, node.move.to_square):
            knight = board.piece_at(knight_square)
            if (
                knight
                and knight.piece_type == KNIGHT
                and (
                    abs(square_rank(knight_square) - square_rank(king)) == 2
                    and abs(square_file(knight_square) - square_file(king)) == 2
                )
            ):
                return True
    return False

def hook_mate(puzzle: Puzzle) -> bool:
    node = puzzle.mainline[-1]
    board = node.board()
    king = board.king(not puzzle.pov)
    assert king is not None
    assert isinstance(node, ChildNode)
    if moved_piece_type(node) == ROOK and square_distance(node.move.to_square, king) == 1:
        for rook_defender_square in board.attackers(puzzle.pov, node.move.to_square):
            defender = board.piece_at(rook_defender_square)
            if defender and defender.piece_type == KNIGHT and square_distance(rook_defender_square, king) == 1:
                for knight_defender_square in board.attackers(puzzle.pov, rook_defender_square):
                    pawn = board.piece_at(knight_defender_square)
                    if pawn and pawn.piece_type == PAWN:
                        return True
    return False

def anastasia_mate(puzzle: Puzzle) -> bool:
    node = puzzle.mainline[-1]
    board = node.board()
    king = board.king(not puzzle.pov)
    assert king is not None
    assert isinstance(node, ChildNode)
    if square_file(king) in [0, 7] and square_rank(king) not in [0, 7]:
        if square_file(node.move.to_square) == square_file(king) and moved_piece_type(node) in [QUEEN, ROOK]:
            if square_file(king) != 0:
                board.apply_transform(chess.flip_horizontal)
            king = board.king(not puzzle.pov)
            assert king is not None
            blocker = board.piece_at(king + 1)
            if blocker is not None and blocker.color != puzzle.pov:
                knight = board.piece_at(king + 3)
                if knight is not None and knight.color == puzzle.pov and knight.piece_type == KNIGHT:
                    return True
    return False

def back_rank_mate(puzzle: Puzzle) -> bool:
    node = puzzle.mainline[-1]
    board = node.board()
    king = board.king(not puzzle.pov)
    assert king is not None
    assert isinstance(node, ChildNode)
    back_rank = 7 if puzzle.pov else 0
    if board.is_checkmate() and square_rank(king) == back_rank:
        squares = SquareSet.from_square(king + (-8 if puzzle.pov else 8))
        if puzzle.pov:
            if chess.square_file(king) < 7:
                squares.add(king - 7)
            if chess.square_file(king) > 0:
                squares.add(king - 9)
        else:
            if chess.square_file(king) < 7:
                squares.add(king + 9)
            if chess.square_file(king) > 0:
                squares.add(king + 7)
        for square in squares:
            piece = board.piece_at(square)
            if piece is None or piece.color == puzzle.pov or board.attackers(puzzle.pov, square):
                return False
        return any(square_rank(checker) == back_rank for checker in board.checkers())
    return False