import logging
import chess
import chess.engine
import copy

from .model import Puzzle, NextMovePair
from chess import Move, Color
from chess.engine import SimpleEngine, Mate, Cp, Score, PovScore
from chess.pgn import Game, ChildNode

from typing import List, Optional, Union, Set
from .util import count_mates, material_count, material_diff, is_up_in_material, maximum_castling_rights
from .engine import win_chances, get_next_move_pair, EVAL_LIMIT, PAIR_LIMIT, MATE_DEFENSE_LIMIT, MATE_SOON

logger = logging.getLogger(__name__)


class Generator:
    def __init__(self, engine: SimpleEngine):
        self.engine = engine
        self.not_analysed_warning = False

    def _make_puzzle(self, node, solution, cp):
        """_summary_

        Args:
            node (_type_): _description_
            solution (_type_): _description_
            cp (_type_): _description_

        Returns:
            _type_: _description_
        """
        parent = node.parent
        fen = parent.board().fen()
        moves = [node.move] + solution
        pov = node.board().turn
        game_url = node.game().headers.get("Site", "")
        game_id = game_url[20:] if len(game_url) > 20 else game_url

        game = chess.pgn.Game()
        game.setup(fen)
        n = game
        for move in moves:
            n = n.add_main_variation(move)
        return Puzzle(fen=fen, moves=moves, cp=cp, pov=pov, node=game, game_id=game_id)

    def is_valid_mate_in_one(self, pair: NextMovePair) -> bool:
        """_summary_

        Args:
            pair (NextMovePair): _description_

        Returns:
            bool: _description_
        """
        if pair.best.score != Mate(1):
            return False
        non_mate_win_threshold = 0.6
        if not pair.second or win_chances(pair.second.score) <= non_mate_win_threshold:
            return True
        if pair.second.score == Mate(1):
            # if there's more than one mate in one, gotta look if the best non-mating move is bad enough
            logger.debug("Looking for best non-mating move...")
            mates = count_mates(copy.deepcopy(pair.node.board()))
            info = self.engine.analyse(pair.node.board(), multipv=mates + 1, limit=PAIR_LIMIT)
            scores = [pv["score"].pov(pair.winner) for pv in info]
            # the first non-matein1 move is the last element
            if scores[-1] < Mate(1) and win_chances(scores[-1]) > non_mate_win_threshold:
                return False
            return True
        return False

    # is pair.best the only continuation?
    def is_valid_attack(self, pair: NextMovePair) -> bool:
        """_summary_

        Args:
            pair (NextMovePair): _description_

        Returns:
            bool: _description_
        """
        return (
            pair.second is None
            or self.is_valid_mate_in_one(pair)
            or win_chances(pair.best.score) > win_chances(pair.second.score) + 0.7
        )

    def get_next_pair(self, node: ChildNode, winner: Color) -> Optional[NextMovePair]:
        """_summary_

        Args:
            node (ChildNode): _description_
            winner (Color): _description_

        Returns:
            Optional[NextMovePair]: _description_
        """
        pair = get_next_move_pair(self.engine, node, winner, PAIR_LIMIT)
        if node.board().turn == winner and not self.is_valid_attack(pair):
            logger.debug("No valid attack {}".format(pair))
            return None
        return pair

    def get_next_move(self, node: ChildNode, limit: chess.engine.Limit) -> Optional[Move]:
        result = self.engine.play(node.board(), limit=limit)
        return result.move if result else None

    def cook_mate(self, node: ChildNode, winner: Color) -> Optional[List[Move]]:
        """_summary_

        Args:
            node (ChildNode): _description_
            winner (Color): _description_

        Returns:
            Optional[List[Move]]: _description_
        """

        board = node.board()

        if board.is_game_over():
            return []

        if board.turn == winner:
            pair = self.get_next_pair(node, winner)
            if not pair:
                return None
            if pair.best.score < MATE_SOON:
                logger.debug("Best move is not a mate, we're probably not searching deep enough")
                return None
            move = pair.best.move
        else:
            next = self.get_next_move(node, MATE_DEFENSE_LIMIT)
            if not next:
                return None
            move = next

        follow_up = self.cook_mate(node.add_main_variation(move), winner)

        if follow_up is None:
            return None

        return [move] + follow_up

    def cook_advantage(self, node: ChildNode, winner: Color) -> Optional[List[NextMovePair]]:
        """_summary_

        Args:
            node (ChildNode): _description_
            winner (Color): _description_

        Returns:
            Optional[List[NextMovePair]]: _description_
        """

        board = node.board()

        if board.is_repetition(2):
            logger.debug("Found repetition, canceling")
            return None

        pair = self.get_next_pair(node, winner)
        if not pair:
            return []
        if pair.best.score < Cp(200):
            logger.debug("Not winning enough, aborting")
            return None

        follow_up = self.cook_advantage(node.add_main_variation(pair.best.move), winner)

        if follow_up is None:
            return None

        return [pair] + follow_up

    def analyze_game(self, game: Game, tier: int, all_puzzles: bool = False) -> list[Puzzle]:

        puzzles = []

        logger.debug(f"Analyzing tier {tier} {game.headers.get('Site')}...")

        prev_score: Score = Cp(20)
        seen_epds: Set[str] = set()
        board = game.board()
        skip_until_irreversible = False

        for node in game.mainline():
            if skip_until_irreversible:
                if board.is_irreversible(node.move):
                    skip_until_irreversible = False
                    seen_epds.clear()
                else:
                    board.push(node.move)
                    continue

            current_eval = node.eval()

            if not current_eval:
                if not self.not_analysed_warning:
                    logger.warning(
                        "Game not already analysed by stockfish, will make one but consider using already analysed games from Lichess"
                    )
                    self.not_analysed_warning = True
                logger.debug("Move without eval on ply {}, computing...".format(node.ply()))
                current_eval = self.engine.analyse(node.board(), EVAL_LIMIT)["score"]

            board.push(node.move)
            epd = board.epd()
            if epd in seen_epds:
                skip_until_irreversible = True
                continue
            seen_epds.add(epd)

            if board.castling_rights != maximum_castling_rights(board):
                continue

            result = self.analyze_position(node, prev_score, current_eval, tier)

            if isinstance(result, Puzzle):
                if not all_puzzles:
                    return [result]
                puzzles.append(result)
                prev_score = Cp(20)
            else:
                prev_score = -result

        if not puzzles:
            logger.debug("Found nothing from {}".format(game.headers.get("Site")))

        return puzzles

    def analyze_position(
        self, node: ChildNode, prev_score: Score, current_eval: PovScore, tier: int
    ) -> Union[Puzzle, Score]:
        """_summary_

        Args:
            node (ChildNode): _description_
            prev_score (Score): _description_
            current_eval (PovScore): _description_
            tier (int): _description_

        Returns:
            Union[Puzzle, Score]: _description_
        """

        board = node.board()
        winner = board.turn
        score = current_eval.pov(winner)

        if board.legal_moves.count() < 2:
            return score

        game_url = node.game().headers.get("Site")

        logger.debug("{} {} to {}".format(node.ply(), node.move.uci() if node.move else None, score))

        if prev_score > Cp(300) and score < MATE_SOON:
            logger.debug(
                "{} Too much of a winning position to start with {} -> {}".format(node.ply(), prev_score, score)
            )
            return score
        if is_up_in_material(board, winner):
            logger.debug(
                "{} already up in material {} {} {}".format(
                    node.ply(), winner, material_count(board, winner), material_count(board, not winner)
                )
            )
            return score
        elif score >= Mate(1) and tier < 3:
            logger.debug("{} mate in one".format(node.ply()))
            return score
        elif score > MATE_SOON:
            logger.debug("Mate {}#{} Probing...".format(game_url, node.ply()))
            mate_solution = self.cook_mate(copy.deepcopy(node), winner)
            if mate_solution is None or (tier == 1 and len(mate_solution) == 3):
                return score
            return self._make_puzzle(node, mate_solution, 999999999)
        elif score >= Cp(200) and win_chances(score) > win_chances(prev_score) + 0.6:
            if score < Cp(400) and material_diff(board, winner) > -1:
                logger.debug("Not clearly winning and not from being down in material, aborting")
                return score
            logger.debug("Advantage {}#{} {} -> {}. Probing...".format(game_url, node.ply(), prev_score, score))
            puzzle_node = copy.deepcopy(node)
            solution: Optional[List[NextMovePair]] = self.cook_advantage(puzzle_node, winner)
            if not solution:
                return score
            while len(solution) % 2 == 0 or not solution[-1].second:
                if not solution[-1].second:
                    logger.debug("Remove final only-move")
                solution = solution[:-1]
            if not solution or len(solution) == 1:
                logger.debug("Discard one-mover")
                return score
            if tier < 3 and len(solution) == 3:
                logger.debug("Discard two-mover")
                return score
            cp = solution[len(solution) - 1].best.score.score()
            return self._make_puzzle(node, [p.best.move for p in solution], 999999998 if cp is None else cp)
        else:
            return score
