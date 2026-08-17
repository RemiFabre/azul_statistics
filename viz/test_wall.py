"""Check viz/wall.py against the repository's own engine.

The figures must not tell a different story from the results they illustrate,
so every score printed on a figure is produced by scoring rules that agree,
board for board, with ``src/board.py``.

    python3 viz/test_wall.py
"""

import copy
import itertools
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from board import Board  # noqa: E402  (the engine, from src/)

import wall  # noqa: E402


def engine_score(grid):
    """Replay a grid through src/board.py, the way adjacent.py does it."""
    colors = ["blue", "yellow", "red", "black", "lightblue"]
    board = Board(0, Board.WALL, Board.SG_AR, 0, False)
    for rnd in range(wall.SIZE):
        for row, spec in enumerate(grid):
            for col, when in enumerate(spec):
                if when != rnd:
                    continue
                stage = copy.deepcopy(Board.SG_AR)
                stage[row] = (stage[row][0], (stage[row][0], colors[(col - row) % 5]))
                board = Board(board.score, board.wall, stage, 0, False).update_score()
    return board.score


def main():
    random.seed(20240128)
    perms = list(itertools.permutations(range(5)))
    cases = []

    # the boards the README actually talks about
    cases += [
        ((0, 1, 2, 3, 4),),
        ((0, 1, 2, 3, 4), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4)),
        ((0, 1, 2, 3, 4), (3, 2, 1, 0, 4), (3, 2, 0, 1, 4)),
        ((0, 2, 1, 4, 3), (1, 2, 0, 4, 3), (0, 1, 4, 3, 2)),
    ]
    # plus a random sweep over one, two and three lines
    for n in (1, 2, 3):
        cases += [tuple(random.choice(perms) for _ in range(n)) for _ in range(120)]

    bad = 0
    for grid in cases:
        mine, theirs = wall.score_of(grid), engine_score(grid)
        if mine != theirs:
            bad += 1
            print(f"MISMATCH {grid}: viz={mine} engine={theirs}")
    print(f"{len(cases) - bad}/{len(cases)} boards agree with src/board.py")

    # the four headline numbers from the README, spelled out
    expected = {
        ((0, 1, 2, 3, 4),): 15,
        ((0, 1, 2, 3, 4), (0, 1, 2, 3, 4), (0, 1, 2, 3, 4)): 68,
        ((0, 1, 2, 3, 4), (3, 2, 1, 0, 4), (3, 2, 0, 1, 4)): 70,
        ((0, 2, 1, 4, 3), (1, 2, 0, 4, 3), (0, 1, 4, 3, 2)): 47,
    }
    for grid, want in expected.items():
        got = wall.score_of(grid)
        flag = "ok" if got == want else "WRONG"
        print(f"  {flag}: {len(grid)} line(s) -> {got} (README says {want})")
        bad += got != want

    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
