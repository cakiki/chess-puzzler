import unittest
import shutil
import chess
import chess.pgn
from chess_puzzler.model import Puzzle
from chess_puzzler.engine import open_engine
from chess_puzzler.tags.zugzwang import zugzwang


def make(id, fen, line, cp=999999998):
    moves = [chess.Move.from_uci(m) for m in line.split()]
    game = chess.pgn.Game()
    game.setup(fen)
    node = game
    for move in moves:
        node = node.add_main_variation(move)
    board = chess.Board(fen)
    board.push(moves[0])
    pov = board.turn
    return Puzzle(fen=fen, moves=moves, cp=cp, pov=pov, node=game, game_id=id)


@unittest.skipUnless(shutil.which("stockfish"), "Stockfish not found")
class TestZugzwang(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = open_engine("stockfish", threads=4)

    @classmethod
    def tearDownClass(cls):
        cls.engine.close()

    def test_zugzwang(self):
        self.assertTrue(
            zugzwang(
                self.engine, make("000o3", "8/2p1k3/6p1/1p1P1p2/1P3P2/3K2Pp/7P/8 b - - 1 43", "e7d6 d3d4 g6g5 f4g5")
            )
        )
        self.assertTrue(
            zugzwang(self.engine, make("00HqY", "8/6p1/8/6k1/4P3/5KpP/8/8 b - - 3 46", "g5h4 f3g2 h4g5 g2g3"))
        )
        self.assertTrue(
            zugzwang(
                self.engine,
                make("00Oyf", "8/1p6/7p/3k1pp1/1P5P/3K1P2/6P1/8 w - - 0 39", "h4g5 h6g5 d3c3 d5e5 c3c4 e5f4 c4c5 f4g3"),
            )
        )

    def test_not_zugzwang(self):
        self.assertFalse(
            zugzwang(
                self.engine,
                make("tMEri", "5r1k/4q1p1/p2pP2p/1p6/1P2Q3/PB6/1BP3PP/6K1 w - - 1 27", "e4g6 e7a7 b2d4 a7d4 g1h1 f8f1"),
            )
        )

        self.assertFalse(
            zugzwang(
                self.engine,
                make(
                    "0018P",
                    "5R2/1p6/p1p5/2P1rk2/2K3p1/2P1p1P1/1P5P/8 b - - 1 44",
                    "f5e6 f8e8 e6f5 e8e5 f5e5 c4d3 e5d5 d3e3 a6a5 e3f4 d5c4 f4g4",
                ),
            )
        )
