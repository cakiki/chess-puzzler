# chess-puzzler

Python package to generate and tag puzzles from chess games. 

## Installation

From pypi:
```bash
pip install chess-puzzler`
```

From source:
```bash
pip install git+https://github.com/cakiki/chess-puzzler.git`
```

### Engine
Finding puzzles and some tagging functions require a UCI-compliant chess engine like [Stockfish](https://stockfishchess.org/download/).

## Usage
You can use chess-puzzler as a CLI tool or as a python library:

### CLI
```bash
puzzler find game.pgn --all --tag
```

### Library
```python
import chess.pgn
from chess_puzzler import Generator, open_engine
from chess_puzzler.tagger import cook

engine = open_engine("stockfish")
game = chess.pgn.read_game(open("game.pgn"))
puzzles = Generator(engine).analyze_game(game, all_puzzles=True)
for puzzle in puzzles:
    puzzle.tags = cook(puzzle, engine=engine)
    print(puzzle.to_dict())
engine.close()
```

> [!IMPORTANT]
> Stockfish is non-deterministic when running multi-threaded. For reproducible results across different runs, make sure to run with `threads=1`.
 
## Inspiration

This is a refactor of [ornicar/lichess-puzzler](https://github.com/ornicar/lichess-puzzler), also inspired by [kraktus/lichess-puzzler](https://github.com/kraktus/lichess-puzzler) and [fitztrev/puzzler](https://github.com/fitztrev/puzzler). The goal was to make the lichess-puzzler more pythonic and pip installable.

## License

`chess-puzzler` is licensed under the GNU Affero General Public License 3 or any later version of your choice.
