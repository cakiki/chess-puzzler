from typing import List, Optional, Tuple

import chess
from chess import Color, Board, Piece, Square, square_file, square_rank, square_distance
from chess.pgn import ChildNode
from chess import KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN

VALUES = {PAWN: 1, KNIGHT: 3, BISHOP: 3, ROOK: 5, QUEEN: 9}
KING_VALUES = {**VALUES, KING: 99}
RAY_PIECE_TYPES = [QUEEN, ROOK, BISHOP]


def moved_piece_type(node: ChildNode) -> chess.PieceType:
    """_summary_

    Args:
        node (ChildNode): _description_

    Returns:
        chess.PieceType: _description_
    """
    pt = node.board().piece_type_at(node.move.to_square)
    assert pt
    return pt


def is_capture(node: ChildNode) -> bool:
    """_summary_

    Args:
        node (ChildNode): _description_

    Returns:
        bool: _description_
    """
    return node.parent.board().is_capture(node.move)


def is_king_move(node: ChildNode) -> bool:
    """_summary_

    Args:
        node (ChildNode): _description_

    Returns:
        bool: _description_
    """
    return moved_piece_type(node) == KING


def is_castling(node: ChildNode) -> bool:
    """_summary_

    Args:
        node (ChildNode): _description_

    Returns:
        bool: _description_
    """
    return is_king_move(node) and square_distance(node.move.from_square, node.move.to_square) > 1


def is_advanced_pawn_move(node: ChildNode) -> bool:
    """_summary_

    Args:
        node (ChildNode): _description_

    Returns:
        bool: _description_
    """
    if node.move.promotion:
        return True
    if moved_piece_type(node) != PAWN:
        return False
    to_rank = square_rank(node.move.to_square)
    return to_rank < 3 if node.turn() else to_rank > 4


def is_very_advanced_pawn_move(node: ChildNode) -> bool:
    """_summary_

    Args:
        node (ChildNode): _description_

    Returns:
        bool: _description_
    """
    if not is_advanced_pawn_move(node):
        return False
    to_rank = square_rank(node.move.to_square)
    return to_rank < 2 if node.turn() else to_rank > 5


def material_count(board: Board, side: Color) -> int:
    """_summary_

    Args:
        board (Board): _description_
        side (Color): _description_

    Returns:
        int: _description_
    """
    return sum(len(board.pieces(piece_type, side)) * value for piece_type, value in VALUES.items())


def material_diff(board: Board, side: Color) -> int:
    """_summary_

    Args:
        board (Board): _description_
        side (Color): _description_

    Returns:
        int: _description_
    """
    return material_count(board, side) - material_count(board, not side)


def is_up_in_material(board: Board, side: Color) -> bool:
    """_summary_

    Args:
        board (Board): _description_
        side (Color): _description_

    Returns:
        bool: _description_
    """
    return material_diff(board, side) > 0


def maximum_castling_rights(board: chess.Board) -> chess.Bitboard:
    """_summary_

    Args:
        board (chess.Board): _description_

    Returns:
        chess.Bitboard: _description_
    """
    return (
        board.pieces_mask(chess.ROOK, chess.WHITE) & (chess.BB_A1 | chess.BB_H1)
        if board.king(chess.WHITE) == chess.E1
        else chess.BB_EMPTY
    ) | (
        board.pieces_mask(chess.ROOK, chess.BLACK) & (chess.BB_A8 | chess.BB_H8)
        if board.king(chess.BLACK) == chess.E8
        else chess.BB_EMPTY
    )


def count_mates(board: chess.Board) -> int:
    """_summary_

    Args:
        board (chess.Board): _description_

    Returns:
        int: _description_
    """
    mates = 0
    for move in board.legal_moves:
        board.push(move)
        if board.is_checkmate():
            mates += 1
        board.pop()
    return mates


def get_next_node(node: ChildNode) -> Optional[ChildNode]:
    """_summary_

    Args:
        node (ChildNode): _description_

    Returns:
        Optional[ChildNode]: _description_
    """
    return node.variations[0] if node.variations else None


def get_next_next_node(node: ChildNode) -> Optional[ChildNode]:
    """_summary_

    Args:
        node (ChildNode): _description_

    Returns:
        Optional[ChildNode]: _description_
    """
    next_node = get_next_node(node)
    return get_next_node(next_node) if next_node else None


def piece_value(piece_type: chess.PieceType) -> int:
    """_summary_

    Args:
        piece_type (chess.PieceType): _description_

    Returns:
        int: _description_
    """
    return VALUES[piece_type]


def attacked_opponent_pieces(board: Board, from_square: Square, pov: Color) -> List[Piece]:
    """_summary_

    Args:
        board (Board): _description_
        from_square (Square): _description_
        pov (Color): _description_

    Returns:
        List[Piece]: _description_
    """
    return [piece for (piece, _) in attacked_opponent_squares(board, from_square, pov)]


def attacked_opponent_squares(board: Board, from_square: Square, pov: Color) -> List[Tuple[Piece, Square]]:
    """_summary_

    Args:
        board (Board): _description_
        from_square (Square): _description_
        pov (Color): _description_

    Returns:
        List[Tuple[Piece, Square]]: _description_
    """
    pieces = []
    for attacked_square in board.attacks(from_square):
        attacked_piece = board.piece_at(attacked_square)
        if attacked_piece and attacked_piece.color != pov:
            pieces.append((attacked_piece, attacked_square))
    return pieces


def is_defended(board: Board, piece: Piece, square: Square) -> bool:
    """_summary_

    Args:
        board (Board): _description_
        piece (Piece): _description_
        square (Square): _description_

    Returns:
        bool: _description_
    """
    if board.attackers(piece.color, square):
        return True
    # ray defense https://lichess.org/editor/6k1/3q1pbp/2b1p1p1/1BPp4/rp1PnP2/4PRNP/4Q1P1/4B1K1_w_-_-_0_1
    for attacker in board.attackers(not piece.color, square):
        attacker_piece = board.piece_at(attacker)
        assert attacker_piece
        if attacker_piece.piece_type in RAY_PIECE_TYPES:
            bc = board.copy(stack=False)
            bc.remove_piece_at(attacker)
            if bc.attackers(piece.color, square):
                return True

    return False


def is_hanging(board: Board, piece: Piece, square: Square) -> bool:
    """_summary_

    Args:
        board (Board): _description_
        piece (Piece): _description_
        square (Square): _description_

    Returns:
        bool: _description_
    """
    return not is_defended(board, piece, square)


def can_be_taken_by_lower_piece(board: Board, piece: Piece, square: Square) -> bool:
    """_summary_

    Args:
        board (Board): _description_
        piece (Piece): _description_
        square (Square): _description_

    Returns:
        bool: _description_
    """
    for attacker_square in board.attackers(not piece.color, square):
        attacker = board.piece_at(attacker_square)
        assert attacker
        if attacker.piece_type != chess.KING and VALUES[attacker.piece_type] < VALUES[piece.piece_type]:
            return True
    return False


def is_in_bad_spot(board: Board, square: Square) -> bool:
    """_summary_

    Args:
        board (Board): _description_
        square (Square): _description_

    Returns:
        bool: _description_
    """
    # hanging or takeable by lower piece
    piece = board.piece_at(square)
    assert piece
    return bool(board.attackers(not piece.color, square)) and (
        is_hanging(board, piece, square) or can_be_taken_by_lower_piece(board, piece, square)
    )


def is_trapped(board: Board, square: Square) -> bool:
    """_summary_

    Args:
        board (Board): _description_
        square (Square): _description_

    Returns:
        bool: _description_
    """
    if board.is_check() or board.is_pinned(board.turn, square):
        return False
    piece = board.piece_at(square)
    assert piece
    if piece.piece_type in [PAWN, KING]:
        return False
    if not is_in_bad_spot(board, square):
        return False
    for escape in board.legal_moves:
        if escape.from_square == square:
            capturing = board.piece_at(escape.to_square)
            if capturing and VALUES[capturing.piece_type] >= VALUES[piece.piece_type]:
                return False
            board.push(escape)
            if not is_in_bad_spot(board, escape.to_square):
                return False
            board.pop()
    return True


def attacker_pieces(board: Board, color: Color, square: Square) -> List[Piece]:
    """_summary_

    Args:
        board (Board): _description_
        color (Color): _description_
        square (Square): _description_

    Returns:
        List[Piece]: _description_
    """
    return [p for p in [board.piece_at(s) for s in board.attackers(color, square)] if p]


def squares_are_collinear(sq1: Square, sq2: Square, sq3: Square) -> bool:
    """_summary_

    Args:
        sq1 (Square): _description_
        sq2 (Square): _description_
        sq3 (Square): _description_

    Returns:
        bool: _description_
    """
    r1, f1 = square_rank(sq1), square_file(sq1)
    r2, f2 = square_rank(sq2), square_file(sq2)
    r3, f3 = square_rank(sq3), square_file(sq3)
    if r1 == r2 == r3:
        return True
    if f1 == f2 == f3:
        return True
    if (r1 - f1) == (r2 - f2) == (r3 - f3):
        return True
    if (r1 + f1) == (r2 + f2) == (r3 + f3):
        return True
    return False
