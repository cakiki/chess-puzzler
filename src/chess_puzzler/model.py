from dataclasses import dataclass, field
from typing import Literal, Optional
from chess import Move, Color
from chess.pgn import GameNode
from chess.engine import Score

TagKind = Literal[
    "advancedPawn",
    "advantage",
    "anastasiaMate",
    "arabianMate",
    "attackingF2F7",
    "attraction",
    "backRankMate",
    "bishopEndgame",
    "bodenMate",
    "capturingDefender",
    "castling",
    "clearance",
    "coercion",
    "collinear",
    "crushing",
    "defensiveMove",
    "discoveredAttack",
    "deflection",
    "doubleBishopMate",
    "doubleCheck",
    "dovetailMate",
    "equality",
    "enPassant",
    "exposedKing",
    "fork",
    "hangingPiece",
    "hookMate",
    "interference",
    "intermezzo",
    "kingsideAttack",
    "knightEndgame",
    "long",
    "mate",
    "mateIn5",
    "mateIn4",
    "mateIn3",
    "mateIn2",
    "mateIn1",
    "oneMove",
    "overloading",
    "pawnEndgame",
    "pin",
    "promotion",
    "queenEndgame",
    "queensideAttack",
    "quietMove",
    "rookEndgame",
    "queenRookEndgame",
    "sacrifice",
    "short",
    "simplification",
    "skewer",
    "smotheredMate",
    "trappedPiece",
    "underPromotion",
    "veryLong",
    "xRayAttack",
    "zugzwang"
]

@dataclass
class Puzzle:
    fen: str
    moves: list[Move]
    cp: int
    pov: Color
    tags: list[TagKind] = field(default_factory=list)
    game_id: str = ""

    def moves_uci(self) -> list[str]:
        return [m.uci() for m in self.moves]
    
@dataclass
class EngineMove:
    move: Move
    score: Score

@dataclass
class NextMovePair:
    node: GameNode
    winner: Color
    best: EngineMove
    second: Optional[EngineMove]
