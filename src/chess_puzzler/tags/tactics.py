import chess
from chess import (
    square_file,
    SquareSet,
    Piece,
    KING,
    QUEEN,
    ROOK,
    PAWN,
)
from chess.pgn import ChildNode


from ..model import Puzzle
from ..util import (
    VALUES,
    KING_VALUES,
    RAY_PIECE_TYPES,
    moved_piece_type,
    is_in_bad_spot,
    is_hanging,
    is_capture,
    get_next_node,
    get_next_next_node,
    is_advanced_pawn_move,
    attacked_opponent_pieces,
    attacked_opponent_squares,
    is_castling,
)


def double_check(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if len(node.board().checkers()) > 1:
            return True
    return False


def x_ray(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        if not is_capture(node):
            continue
        prev_op_node = node.parent
        assert isinstance(prev_op_node, ChildNode)
        if prev_op_node.move.to_square != node.move.to_square or moved_piece_type(prev_op_node) == KING:
            continue
        prev_pl_node = prev_op_node.parent
        assert isinstance(prev_pl_node, ChildNode)
        if prev_pl_node.move.to_square != prev_op_node.move.to_square:
            continue
        if prev_op_node.move.from_square in SquareSet.between(node.move.from_square, node.move.to_square):
            return True

    return False


def fork(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][:-1]:
        if moved_piece_type(node) is not KING:
            board = node.board()
            if is_in_bad_spot(board, node.move.to_square):
                continue
            nb = 0
            for piece, square in attacked_opponent_squares(board, node.move.to_square, puzzle.pov):
                if piece.piece_type == PAWN:
                    continue
                if KING_VALUES[piece.piece_type] > KING_VALUES[moved_piece_type(node)] or (
                    is_hanging(board, piece, square)
                    and square not in board.attackers(not puzzle.pov, node.move.to_square)
                ):
                    nb += 1
            if nb > 1:
                return True
    return False


def overloading(puzzle: Puzzle) -> bool:
    return False


def discovered_attack(puzzle: Puzzle) -> bool:
    if discovered_check(puzzle):
        return True
    for node in puzzle.mainline[1::2][1:]:
        if is_capture(node):
            between = SquareSet.between(node.move.from_square, node.move.to_square)
            assert isinstance(node.parent, ChildNode)
            if node.parent.move.to_square == node.move.to_square:
                return False
            prev = node.parent.parent
            assert isinstance(prev, ChildNode)
            if (
                prev.move.from_square in between
                and node.move.to_square != prev.move.to_square
                and node.move.from_square != prev.move.to_square
                and not is_castling(prev)
            ):
                return True
    return False


def discovered_check(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        board = node.board()
        checkers = board.checkers()
        if checkers and not node.move.to_square in checkers:
            return True
    return False


def quiet_move(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline:
        if (
            # on player move, not the last move of the puzzle
            node.turn() != puzzle.pov
            and not node.is_end()
            and
            # no check given or escaped
            not node.board().is_check()
            and not node.parent.board().is_check()
            and
            # no capture made or threatened
            not is_capture(node)
            and not attacked_opponent_pieces(node.board(), node.move.to_square, puzzle.pov)
            and
            # no advanced pawn push
            not is_advanced_pawn_move(node)
            and moved_piece_type(node) != KING
        ):
            return True
    return False


def defensive_move(puzzle: Puzzle) -> bool:
    # like quiet_move, but on last move
    # at least 3 legal moves
    if puzzle.mainline[-2].board().legal_moves.count() < 3:
        return False
    node = puzzle.mainline[-1]
    # no check given, no piece taken
    if node.board().is_check() or is_capture(node):
        return False
    # no piece attacked
    if attacked_opponent_pieces(node.board(), node.move.to_square, puzzle.pov):
        return False
    # no advanced pawn push
    return not is_advanced_pawn_move(node)


def check_escape(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if node.board().is_check() or is_capture(node):
            return False
        if node.parent.board().legal_moves.count() < 3:
            return False
        if node.parent.board().is_check():
            return True
    return False


def attraction(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1:]:
        if node.turn() == puzzle.pov:
            continue
        # 1. player moves to a square
        first_move_to = node.move.to_square
        opponent_reply = get_next_node(node)
        # 2. opponent captures on that square
        if opponent_reply and opponent_reply.move.to_square == first_move_to:
            attracted_piece = moved_piece_type(opponent_reply)
            if attracted_piece in [KING, QUEEN, ROOK]:
                attracted_to_square = opponent_reply.move.to_square
                next_node = get_next_node(opponent_reply)
                if next_node:
                    attackers = next_node.board().attackers(puzzle.pov, attracted_to_square)
                    # 3. player attacks that square
                    if next_node.move.to_square in attackers:
                        # 4. player checks on that square
                        if attracted_piece == KING:
                            return True
                        n3 = get_next_next_node(next_node)
                        # 4. or player later captures on that square
                        if n3 and n3.move.to_square == attracted_to_square:
                            return True
    return False


def deflection(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        captured_piece = node.parent.board().piece_at(node.move.to_square)
        if captured_piece or node.move.promotion:
            capturing_piece = moved_piece_type(node)
            if captured_piece and KING_VALUES[captured_piece.piece_type] > KING_VALUES[capturing_piece]:
                continue
            square = node.move.to_square
            prev_op_move = node.parent.move
            assert prev_op_move
            grandpa = node.parent.parent
            assert isinstance(grandpa, ChildNode)
            prev_player_move = grandpa.move
            prev_player_capture = grandpa.parent.board().piece_at(prev_player_move.to_square)
            if (
                (not prev_player_capture or VALUES[prev_player_capture.piece_type] < moved_piece_type(grandpa))
                and square != prev_op_move.to_square
                and square != prev_player_move.to_square
                and (prev_op_move.to_square == prev_player_move.to_square or grandpa.board().is_check())
                and (
                    square in grandpa.board().attacks(prev_op_move.from_square)
                    or node.move.promotion
                    and square_file(node.move.to_square) == square_file(prev_op_move.from_square)
                    and node.move.from_square in grandpa.board().attacks(prev_op_move.from_square)
                )
                and (not square in node.parent.board().attacks(prev_op_move.to_square))
            ):
                return True
    return False


def exposed_king(puzzle: Puzzle) -> bool:
    if puzzle.pov:
        pov = puzzle.pov
        board = puzzle.mainline[0].board()
    else:
        pov = not puzzle.pov
        board = puzzle.mainline[0].board().mirror()
    king = board.king(not pov)
    assert king is not None
    if chess.square_rank(king) < 5:
        return False
    squares = SquareSet.from_square(king - 8)
    if chess.square_file(king) > 0:
        squares.add(king - 1)
        squares.add(king - 9)
    if chess.square_file(king) < 7:
        squares.add(king + 1)
        squares.add(king - 7)
    for square in squares:
        if board.piece_at(square) == Piece(PAWN, not pov):
            return False
    for node in puzzle.mainline[1::2][1:-1]:
        if node.board().is_check():
            return True
    return False


def skewer(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        prev = node.parent
        assert isinstance(prev, ChildNode)
        capture = prev.board().piece_at(node.move.to_square)
        if capture and moved_piece_type(node) in RAY_PIECE_TYPES and not node.board().is_checkmate():
            between = SquareSet.between(node.move.from_square, node.move.to_square)
            op_move = prev.move
            assert op_move
            if op_move.to_square == node.move.to_square or not op_move.from_square in between:
                continue
            if KING_VALUES[moved_piece_type(prev)] > KING_VALUES[capture.piece_type] and is_in_bad_spot(
                prev.board(), node.move.to_square
            ):
                return True
    return False


def self_interference(puzzle: Puzzle) -> bool:
    # intereference by opponent piece
    for node in puzzle.mainline[1::2][1:]:
        prev_board = node.parent.board()
        square = node.move.to_square
        capture = prev_board.piece_at(square)
        if capture and is_hanging(prev_board, capture, square):
            grandpa = node.parent.parent
            assert grandpa
            init_board = grandpa.board()
            defenders = init_board.attackers(capture.color, square)
            defender = defenders.pop() if defenders else None
            defender_piece = init_board.piece_at(defender) if defender else None
            if defender and defender_piece and defender_piece.piece_type in RAY_PIECE_TYPES:
                if node.parent.move and node.parent.move.to_square in SquareSet.between(square, defender):
                    return True
    return False


def interference(puzzle: Puzzle) -> bool:
    # intereference by player piece
    for node in puzzle.mainline[1::2][1:]:
        prev_board = node.parent.board()
        square = node.move.to_square
        capture = prev_board.piece_at(square)
        assert node.parent.move
        if capture and square != node.parent.move.to_square and is_hanging(prev_board, capture, square):
            assert node.parent
            assert node.parent.parent
            assert node.parent.parent.parent
            init_board = node.parent.parent.parent.board()
            defenders = init_board.attackers(capture.color, square)
            defender = defenders.pop() if defenders else None
            defender_piece = init_board.piece_at(defender) if defender else None
            if defender and defender_piece and defender_piece.piece_type in RAY_PIECE_TYPES:
                interfering = node.parent.parent
                if interfering.move and interfering.move.to_square in SquareSet.between(square, defender):
                    return True
    return False


def intermezzo(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        if is_capture(node):
            capture_move = node.move
            capture_square = node.move.to_square
            op_node = node.parent
            assert isinstance(op_node, ChildNode)
            prev_pov_node = node.parent.parent
            assert isinstance(prev_pov_node, ChildNode)
            if not op_node.move.from_square in prev_pov_node.board().attackers(not puzzle.pov, capture_square):
                if prev_pov_node.move.to_square != capture_square:
                    prev_op_node = prev_pov_node.parent
                    assert isinstance(prev_op_node, ChildNode)
                    return (
                        prev_op_node.move.to_square == capture_square
                        and is_capture(prev_op_node)
                        and capture_move in prev_op_node.board().legal_moves
                    )
    return False


# the pinned piece can't attack a player piece
def pin_prevents_attack(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        board = node.board()
        for square, piece in board.piece_map().items():
            if piece.color == puzzle.pov:
                continue
            pin_dir = board.pin(piece.color, square)
            if pin_dir == chess.BB_ALL:
                continue
            for attack in board.attacks(square):
                attacked = board.piece_at(attack)
                if (
                    attacked
                    and attacked.color == puzzle.pov
                    and not attack in pin_dir
                    and (VALUES[attacked.piece_type] > VALUES[piece.piece_type] or is_hanging(board, attacked, attack))
                ):
                    return True
    return False


# the pinned piece can't escape the attack
def pin_prevents_escape(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        board = node.board()
        for pinned_square, pinned_piece in board.piece_map().items():
            if pinned_piece.color == puzzle.pov:
                continue
            pin_dir = board.pin(pinned_piece.color, pinned_square)
            if pin_dir == chess.BB_ALL:
                continue
            for attacker_square in board.attackers(puzzle.pov, pinned_square):
                if attacker_square in pin_dir:
                    attacker = board.piece_at(attacker_square)
                    assert attacker
                    if VALUES[pinned_piece.piece_type] > VALUES[attacker.piece_type]:
                        return True
                    if (
                        is_hanging(board, pinned_piece, pinned_square)
                        and pinned_square not in board.attackers(not puzzle.pov, attacker_square)
                        and [
                            m
                            for m in board.pseudo_legal_moves
                            if m.from_square == pinned_square and m.to_square not in pin_dir
                        ]
                    ):
                        return True
    return False


def clearance(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        board = node.board()
        if not node.parent.board().piece_at(node.move.to_square):
            piece = board.piece_at(node.move.to_square)
            if piece and piece.piece_type in RAY_PIECE_TYPES:
                prev = node.parent.parent
                assert prev
                prev_move = prev.move
                assert prev_move
                assert isinstance(node.parent, ChildNode)
                if (
                    not prev_move.promotion
                    and prev_move.to_square != node.move.from_square
                    and prev_move.to_square != node.move.to_square
                    and not node.parent.board().is_check()
                    and (not board.is_check() or moved_piece_type(node.parent) != KING)
                ):
                    if prev_move.from_square == node.move.to_square or prev_move.from_square in SquareSet.between(
                        node.move.from_square, node.move.to_square
                    ):
                        if (
                            prev.parent
                            and not prev.parent.board().piece_at(prev_move.to_square)
                            or is_in_bad_spot(prev.board(), prev_move.to_square)
                        ):
                            return True
    return False


def capturing_defender(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        board = node.board()
        capture = node.parent.board().piece_at(node.move.to_square)
        assert isinstance(node.parent, ChildNode)
        if board.is_checkmate() or (
            capture
            and moved_piece_type(node) != KING
            and VALUES[capture.piece_type] <= VALUES[moved_piece_type(node)]
            and is_hanging(node.parent.board(), capture, node.move.to_square)
            and node.parent.move.to_square != node.move.to_square
        ):
            prev = node.parent.parent
            assert isinstance(prev, ChildNode)
            if not prev.board().is_check() and prev.move.to_square != node.move.from_square:
                assert prev.parent
                init_board = prev.parent.board()
                defender_square = prev.move.to_square
                defender = init_board.piece_at(defender_square)
                if (
                    defender
                    and defender_square in init_board.attackers(defender.color, node.move.to_square)
                    and not init_board.is_check()
                ):
                    return True
    return False
