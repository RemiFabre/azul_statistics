"""The Azul wall, its colours, and its scoring, in about fifty lines.

The README's notation is a grid of round numbers: one row per pattern line,
and the number in column ``c`` is the round in which that column's tile reached
the wall. So::

    (0, 1, 2, 3, 4)
    (3, 2, 1, 0, 4)

means "round 0 put a tile in row 0 column 0 and row 1 column 3", and so on.

``play`` turns such a grid into the sequence of five board states, with the
points each round earned. That is all the figure generator needs.

The scoring here is checked against the repository's own engine (``src/``) by
``test_wall.py``; it is reimplemented rather than imported so that the figures
do not depend on the game engine's global module layout.
"""

from __future__ import annotations

SIZE = 5

# Round numbers are drawn on tiles; a wall square's colour is fixed by where it
# is. Row 0 is blue, yellow, red, black, ice; every row below shifts right by
# one. Same formula the engine uses (`colors[(col - line) % 5]`).
def color_at(row: int, col: int) -> int:
    return (col - row) % SIZE


def points_for(placed: set[tuple[int, int]], row: int, col: int) -> int:
    """Points for putting a tile at (row, col), given what is already placed.

    A tile scores the length of its horizontal run if it has any horizontal
    neighbour, plus the length of its vertical run if it has any vertical one,
    and 1 if it is alone. So a tile with a neighbour in *both* directions is
    counted twice, which is the whole subject of the README.
    """
    def run(dr: int, dc: int) -> int:
        n, r, c = 0, row + dr, col + dc
        while 0 <= r < SIZE and 0 <= c < SIZE and (r, c) in placed:
            n += 1
            r, c = r + dr, c + dc
        return n

    horizontal = run(0, -1) + run(0, 1)
    vertical = run(-1, 0) + run(1, 0)
    both = 1 if horizontal and vertical else 0
    return 1 + horizontal + vertical + both


class Frame:
    """One board state: what is on the wall, and what it is worth."""

    def __init__(self, rnd, placed, stamps, fresh, score, gained,
                 last=0, closes_round=True):
        self.round = rnd                 # -1 for the empty starting board
        self.placed = placed             # {(row, col)}
        self.stamps = stamps             # {(row, col): round it was placed}
        self.fresh = fresh               # the tiles that just landed
        self.score = score               # cumulative
        self.gained = gained             # what this round has added so far
        self.last = last                 # what the tile that just landed scored
        self.closes_round = closes_round  # was that the last tile of the round?


def steps(grid, rounds: int = SIZE):
    """Replay a filling one tile at a time, in the order the wall receives them.

    ``grid`` is a sequence of rows; each row is a sequence of 5 entries, where
    an ``int`` is the round that column is filled in and ``None`` means never.

    Within a round the wall is filled top row first, exactly as the engine does
    it (``help_score_staging`` walks the pattern lines downwards). That is the
    single most important fact in this repository, so the animations show it:
    each tile lands on its own frame.

    The first frame is the empty board.
    """
    placed: set[tuple[int, int]] = set()
    stamps: dict[tuple[int, int], int] = {}
    score = 0
    out = [Frame(-1, set(), {}, set(), 0, 0)]

    for rnd in range(rounds):
        landing = sorted((row, col)
                         for row, spec in enumerate(grid)
                         for col, when in enumerate(spec) if when == rnd)
        gained = 0
        for i, (row, col) in enumerate(landing):
            points = points_for(placed, row, col)
            placed.add((row, col))
            stamps[(row, col)] = rnd
            score += points
            gained += points
            out.append(Frame(rnd, set(placed), dict(stamps), {(row, col)},
                             score, gained, last=points,
                             closes_round=(i == len(landing) - 1)))
    return out


def play(grid, rounds: int = SIZE):
    """The same replay, one frame per round instead of one per tile."""
    frames = [f for f in steps(grid, rounds) if f.closes_round]
    for f in frames[1:]:
        f.fresh = {p for p, r in f.stamps.items() if r == f.round}
    return frames


def still(stamps: dict, *, score: int = 0, gained: int = 0, fresh=()) -> Frame:
    """A hand-built board, for figures that illustrate a rule rather than a run."""
    return Frame(0, set(stamps), dict(stamps), set(fresh), score, gained)


def parse(text: str):
    """Read a grid the way the README writes it.

    Accepts the two notations that appear in the results files::

        (0, 1, 2, 3, 4)          -> rounds
        ('0', 'X', 'X', 'X', 'X') -> round 0, and "some later round" for X

    ``X`` becomes ``None``: the figures for starting positions show only the
    tiles of round 0, and leave the rest of the wall empty.
    """
    grid = []
    for line in text.strip().splitlines():
        line = line.strip().strip("()").replace("'", "").replace('"', "")
        if not line:
            continue
        grid.append(tuple(None if x.strip() == "X" else int(x) for x in line.split(",")))
    return tuple(grid)


def score_of(grid) -> int:
    return play(grid)[-1].score
