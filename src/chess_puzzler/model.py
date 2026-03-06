from dataclasses import dataclass, field
from typing import Optional
from chess import Move, Color
from chess.pgn import GameNode
from chess.engine import Score

@dataclass
class Puzzle:
    fen: str
    moves: list[Move]
    cp: int
    pov: Color
    tags: list[str] = field(default_factory=list)
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
