from dataclasses import dataclass, field
from typing import Optional
from chess import Move, Color
from chess.pgn import GameNode, ChildNode
from chess.engine import Score


@dataclass
class Puzzle:
    fen: str
    moves: list[Move]
    cp: int
    pov: Color
    node: Optional[GameNode] = field(default=None, repr=False)
    tags: list[str] = field(default_factory=list)
    game_id: str = ""

    @property
    def mainline(self) -> list[ChildNode]:
        return list(self.node.mainline()) if self.node else []

    def moves_uci(self) -> list[str]:
        return [m.uci() for m in self.moves]

    def to_dict(self) -> dict:
        return {
            "fen": self.fen,
            "moves": self.moves_uci(),
            "cp": self.cp,
            "pov": "white" if self.pov else "black",
            "game_id": self.game_id,
            "tags": self.tags,
        }


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
