from typing import List, Optional
from chess import (
    QUEEN,
    ROOK,
    BISHOP,
    KNIGHT,
    PAWN,
)
from chess.engine import SimpleEngine


from .tags.endgame import piece_endgame, queen_rook_endgame
from .tags.mate import (
    anastasia_mate,
    arabian_mate,
    back_rank_mate,
    boden_or_double_bishop_mate,
    dovetail_mate,
    hook_mate,
    mate_in,
    smothered_mate,
)
from .tags.material import hanging_piece, sacrifice, trapped_piece
from .tags.misc import (
    advanced_pawn,
    attacking_f2_f7,
    castling,
    en_passant,
    kingside_attack,
    promotion,
    queenside_attack,
    under_promotion,
)
from .tags.tactics import (
    attraction,
    capturing_defender,
    check_escape,
    clearance,
    defensive_move,
    deflection,
    discovered_attack,
    double_check,
    exposed_king,
    fork,
    interference,
    intermezzo,
    overloading,
    pin_prevents_attack,
    pin_prevents_escape,
    quiet_move,
    self_interference,
    skewer,
    x_ray,
)
from .model import Puzzle


def cook(puzzle: Puzzle, engine: Optional[SimpleEngine] = None) -> List[str]:
    """_summary_

    Args:
        puzzle (Puzzle): _description_
        engine (Optional[SimpleEngine], optional): _description_. Defaults to None.

    Returns:
        List[str]: _description_
    """
    tags = []

    mate_tag = mate_in(puzzle)
    if mate_tag:
        tags.append(mate_tag)
        tags.append("mate")
        if smothered_mate(puzzle):
            tags.append("smotheredMate")
        elif back_rank_mate(puzzle):
            tags.append("backRankMate")
        elif anastasia_mate(puzzle):
            tags.append("anastasiaMate")
        elif hook_mate(puzzle):
            tags.append("hookMate")
        elif arabian_mate(puzzle):
            tags.append("arabianMate")
        else:
            found = boden_or_double_bishop_mate(puzzle)
            if found:
                tags.append(found)
            elif dovetail_mate(puzzle):
                tags.append("dovetailMate")
    elif puzzle.cp > 600:
        tags.append("crushing")
    elif puzzle.cp > 200:
        tags.append("advantage")
    else:
        tags.append("equality")

    if attraction(puzzle):
        tags.append("attraction")

    if deflection(puzzle):
        tags.append("deflection")
    elif overloading(puzzle):
        tags.append("overloading")

    if advanced_pawn(puzzle):
        tags.append("advancedPawn")

    if double_check(puzzle):
        tags.append("doubleCheck")

    if quiet_move(puzzle):
        tags.append("quietMove")

    if defensive_move(puzzle) or check_escape(puzzle):
        tags.append("defensiveMove")

    if sacrifice(puzzle):
        tags.append("sacrifice")

    if x_ray(puzzle):
        tags.append("xRayAttack")

    if fork(puzzle):
        tags.append("fork")

    if hanging_piece(puzzle):
        tags.append("hangingPiece")

    if trapped_piece(puzzle):
        tags.append("trappedPiece")

    if discovered_attack(puzzle):
        tags.append("discoveredAttack")

    if exposed_king(puzzle):
        tags.append("exposedKing")

    if skewer(puzzle):
        tags.append("skewer")

    if self_interference(puzzle) or interference(puzzle):
        tags.append("interference")

    if intermezzo(puzzle):
        tags.append("intermezzo")

    if pin_prevents_attack(puzzle) or pin_prevents_escape(puzzle):
        tags.append("pin")

    if attacking_f2_f7(puzzle):
        tags.append("attackingF2F7")

    if clearance(puzzle):
        tags.append("clearance")

    if en_passant(puzzle):
        tags.append("enPassant")

    if castling(puzzle):
        tags.append("castling")

    if promotion(puzzle):
        tags.append("promotion")

    if under_promotion(puzzle):
        tags.append("underPromotion")

    if capturing_defender(puzzle):
        tags.append("capturingDefender")

    if piece_endgame(puzzle, PAWN):
        tags.append("pawnEndgame")
    elif piece_endgame(puzzle, QUEEN):
        tags.append("queenEndgame")
    elif piece_endgame(puzzle, ROOK):
        tags.append("rookEndgame")
    elif piece_endgame(puzzle, BISHOP):
        tags.append("bishopEndgame")
    elif piece_endgame(puzzle, KNIGHT):
        tags.append("knightEndgame")
    elif queen_rook_endgame(puzzle):
        tags.append("queenRookEndgame")

    if "backRankMate" not in tags and "fork" not in tags:
        if kingside_attack(puzzle):
            tags.append("kingsideAttack")
        elif queenside_attack(puzzle):
            tags.append("queensideAttack")

    if len(puzzle.mainline) == 2:
        tags.append("oneMove")
    elif len(puzzle.mainline) == 4:
        tags.append("short")
    elif len(puzzle.mainline) >= 8:
        tags.append("veryLong")
    else:
        tags.append("long")

    if engine:
        from .tags.zugzwang import zugzwang

        if zugzwang(engine, puzzle):
            tags.append("zugzwang")
    return tags
