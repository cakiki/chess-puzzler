from .model import Puzzle
from .tags import ALL_TAGS


def tag(puzzle: Puzzle) -> list[str]:
    tags: list[str] = []
    for t in ALL_TAGS:
        result = t(puzzle)
        if isinstance(result, list):
            tags.extend(result)
        elif result:
            tags.append(result)
    puzzle.tags = tags
    return tags
