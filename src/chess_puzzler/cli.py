import json
import logging
import sys
from pathlib import Path

import chess.pgn
import click

from .engine import open_engine
from .finder import Generator

logger = logging.getLogger("chess_puzzler")


@click.group()
def main():
    pass


@main.command()
@click.argument("pgn", type=click.Path(exists=True, path_type=Path))
@click.option("--engine", "-e", default="stockfish")
@click.option("--threads", "-t", default=4, type=int)
@click.option("--output", "-o", type=click.Path(path_type=Path))
@click.option("--tier", default=10, type=int)
@click.option("-v", "--verbose", count=True)
@click.option("--tag", is_flag=True, help="Also tag puzzles")
def find(pgn, engine, threads, output, tier, verbose, tag):
    logging.basicConfig(format="%(asctime)s %(levelname)-4s %(message)s", datefmt="%m/%d %H:%M")
    logger.setLevel(logging.DEBUG if verbose >= 2 else logging.INFO if verbose else logging.WARNING)

    eng = open_engine(engine, threads)
    generator = Generator(eng)
    out = open(output, "w") if output else sys.stdout

    try:
        with open(pgn) as f:
            game_num = 0
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                game_num += 1
                logger.info(f"Game {game_num}: {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}")

                try:
                    puzzle = generator.analyze_game(game, tier)
                    if puzzle:
                        if tag:
                            from .tagger import cook
                            puzzle.tags = cook(puzzle)
                        out.write(
                            json.dumps(
                                {
                                    "fen": puzzle.fen,
                                    "moves": puzzle.moves_uci(),
                                    "cp": puzzle.cp,
                                    "pov": "white" if puzzle.pov else "black",
                                    "game_id": puzzle.game_id,
                                    "tags": puzzle.tags
                                }
                            )
                            + "\n"
                        )
                        if out == sys.stdout:
                            out.flush()
                        logger.info(f"  Puzzle: {puzzle.fen[:30]}... ({len(puzzle.moves)} moves)")
                except Exception as e:
                    logger.error(f"  Error: {e}")
    finally:
        eng.close()
        if out != sys.stdout:
            out.close()

if __name__ == "__main__":
    main()
