"""Brute-force every order in which the top rows of an Azul wall can be filled.

Everything here drives the engine in the rest of this directory; the only thing
it adds is the enumeration and the bookkeeping.

    python3 src/adjacent.py lines 1        # 120 orders          (a second)
    python3 src/adjacent.py lines 2        # 14 400 orders       (a few seconds)
    python3 src/adjacent.py lines 3        # 1 728 000 orders    (~5 minutes)
    python3 src/adjacent.py starters 3     # openings, from the files above
    python3 src/adjacent.py plot 3         # matplotlib histogram, on screen
    python3 src/adjacent.py demo           # print a board or two, as a sanity check

`lines N` writes results/N_lines_scores.txt and the best/worst combination
files; `starters N` writes the best/worst starter files. The figures in the
README are drawn from those same files by ../viz/make_figures.py. See
../viz/README.md.

A "filling" is written as one tuple per wall row, where the number in column c
is the round in which that column was filled:

    (0, 1, 2, 3, 4)      round 0 filled column 0, round 1 filled column 1, ...
    (2, 0, 1, 3, 4)
"""

import argparse
import ast
import copy
import sys
from itertools import permutations, product
from pathlib import Path

from board import *
from factory import *
from player import *
from state import *
from tile import *

RESULTS = Path(__file__).resolve().parent.parent / "results"
LINE_SIZE = 5


def place_and_score(board, line, col, verbose=False):
    """Put one tile on the wall at (line, col) and let the engine score it."""
    colors = ["blue", "yellow", "red", "black", "lightblue"]
    color = colors[(col - line) % 5]
    stage = copy.deepcopy(Board.SG_AR)
    stage[line] = (stage[line][0], (stage[line][0], color))
    board = Board(board.score, board.wall, stage, 0, False)
    board = board.update_score()

    if verbose:
        print(boards_to_str([board]))
    return board


def demo():
    """Print a fresh board, then two hand-made fillings, to check the engine."""
    board = Board(0, Board.WALL, Board.SG_AR, 0, False)
    print(boards_to_str([board]))

    board = place_and_score(board, 0, 0)
    board = place_and_score(board, 1, 0)
    board = place_and_score(board, 2, 2)
    print(boards_to_str([board]))

    board = Board(0, Board.WALL, Board.SG_AR, 0, False)
    for i in range(LINE_SIZE):
        board = place_and_score(board, 0, i)
        board = place_and_score(board, 1, i)
    print(boards_to_str([board]))


def brute_force(num_lines, line_size=LINE_SIZE, progress=True):
    """Score every way of filling `num_lines` lines of `line_size` tiles.

    One permutation per line: the tuple says, for each column, which round
    fills it. Rounds happen in order, and within a round the wall is filled
    from the top line down. That ordering is what makes the answer interesting,
    and it is the engine's, not ours.

    Returns (sorted scores, {score: [the fillings that reach it]}).
    """
    perms = list(permutations(range(line_size)))
    total = len(perms) ** num_lines

    scores = []
    histories = {}
    for i, fillings in enumerate(product(perms, repeat=num_lines)):
        board = Board(0, Board.WALL, Board.SG_AR, 0, False)
        for round in range(line_size):
            for line, filling in enumerate(fillings):
                board = place_and_score(board, line, filling.index(round))

        scores.append(board.score)
        histories.setdefault(board.score, []).append(fillings)

        if progress and (i + 1) % 10000 == 0:
            print(f"completion: {i + 1}/{total}", end="\r", flush=True)

    if progress:
        print(f"completion: {total}/{total}")
    return sorted(scores), histories


def plot_scores(scores, num_lines, out=None):
    """The score histogram. Pass `out` to write a file instead of showing it.

    The README's charts are not made here. ../viz/make_figures.py draws them
    from the scores file, in the same style as the board figures.
    """
    import matplotlib.pyplot as plt
    import numpy as np

    bin_edges = np.arange(min(scores) - 0.5, max(scores) + 1.5, 1)

    plt.hist(scores, bins=bin_edges, edgecolor="black")
    plt.title(
        f"Frequency of Each Score when filling {num_lines} lines in Azul ({len(scores)} scores)"
    )
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.xticks(range(min(scores), max(scores) + 1))

    if out:
        plt.savefig(out, dpi=110, bbox_inches="tight")
        print(f"wrote {out}")
    else:
        plt.show()


def format_histories(histories, num_lines, which):
    """The best (or worst) fillings, in the layout the results files use."""
    assert which in ("maximum", "minimum")
    nb_boards = sum(len(v) for v in histories.values())
    score = max(histories) if which == "maximum" else min(histories)
    chosen = histories[score]

    out = [
        f"All of the combinations that score the {which} score for "
        f"{num_lines} lines: {score} points",
        f"There are {len(chosen)} ways of doing it out of {nb_boards}, "
        f"that's {len(chosen)/nb_boards*100:.3f}%",
    ]
    for history in chosen:
        out += [str(line) for line in history]
        out.append("")
    return "\n".join(out)


def analyze_histories(histories, num_lines, write=True):
    """Report the best and worst fillings; optionally write them to results/."""
    for which, name in (("maximum", "best"), ("minimum", "worst")):
        text = format_histories(histories, num_lines, which)
        print(text[: text.index("\n", text.index("\n") + 1)])
        if write:
            path = RESULTS / f"{num_lines}_lines_{name}_combinations.txt"
            path.write_text(text)
            print(f"wrote {path}")


def process_and_count_groups(groups):
    """Reduce fillings to their opening (round 0 only) and count duplicates."""
    processed_groups_count = {}
    for group in groups:
        processed_group = tuple(
            tuple("0" if num == 0 else "X" for num in row) for row in group
        )
        processed_groups_count[processed_group] = (
            processed_groups_count.get(processed_group, 0) + 1
        )
    return dict(
        sorted(processed_groups_count.items(), key=lambda item: item[1], reverse=True)
    )


def read_data_from_file(file_path):
    """Read the tuples out of a combinations file, grouped by blank lines."""
    with open(file_path, "r") as file:
        groups = []
        current_group = []
        for line in file:
            if line.startswith("("):  # Start of a new tuple
                current_group.append(tuple(map(int, line.strip("()\n").split(", "))))
            elif line.strip() == "" and current_group:  # Empty line, group is complete
                groups.append(tuple(current_group))
                current_group = []
        if current_group:  # Add the last group if file doesn't end with an empty line
            groups.append(tuple(current_group))

    return groups


STARTER_HEADER = {
    "best": (
        "These are all the unique starting position that can yield the maximum "
        "amount of points for {num_lines} lines ({score} points).\n"
        "They are ranked by the number of duplicates, i.e. the number of "
        "combinations that started with this opening.\n"
        "The higher the number, the more probable it is to reach the highest score.\n"
    ),
    "worst": (
        "These are all the unique starting position that can yield the lowest "
        "amount of points for {num_lines} lines ({score} points)\n"
        "They are ranked by the number of duplicates, i.e. the number of "
        "combinations that started with this opening.\n"
        "The higher the number, the more probable it is to reach the lowest score.\n"
    ),
}


def starting_positions(num_lines, write=True):
    """Turn the best/worst combination files into best/worst starter files."""
    for name in ("best", "worst"):
        source = RESULTS / f"{num_lines}_lines_{name}_combinations.txt"
        if not source.exists():
            sys.exit(f"{source} is missing. Run `lines {num_lines}` first")
        score = int(source.read_text().split(":")[1].split()[0])
        counts = process_and_count_groups(read_data_from_file(source))

        lines = [STARTER_HEADER[name].format(num_lines=num_lines, score=score)]
        for group, count in counts.items():
            lines.append(f"Number of duplicates: {count}")
            lines += [str(line) for line in group]
            lines.append("")
        text = "\n".join(lines)

        print(f"{name}: {len(counts)} unique openings")
        if write:
            path = RESULTS / f"{num_lines}_lines_{name}_starters.txt"
            path.write_text(text)
            print(f"wrote {path}")


def run_lines(num_lines, write=True):
    scores, histories = brute_force(num_lines)
    if write:
        path = RESULTS / f"{num_lines}_lines_scores.txt"
        path.write_text(f"{len(scores)}\n{scores}\n")
        print(f"wrote {path}")
    analyze_histories(histories, num_lines, write=write)
    return scores, histories


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("lines", help="brute-force N lines and write results/")
    p.add_argument("num_lines", type=int, choices=(1, 2, 3, 4, 5))
    p.add_argument("--no-write", action="store_true", help="print only")

    p = sub.add_parser("starters", help="derive the openings from the results files")
    p.add_argument("num_lines", type=int, choices=(1, 2, 3, 4, 5))
    p.add_argument("--no-write", action="store_true", help="print only")

    p = sub.add_parser("plot", help="matplotlib histogram of a scores file")
    p.add_argument("num_lines", type=int, choices=(1, 2, 3, 4, 5))
    p.add_argument("--out", help="write to this path instead of opening a window")

    sub.add_parser("demo", help="print a few boards to check the engine")

    args = parser.parse_args(argv)

    if args.command == "lines":
        run_lines(args.num_lines, write=not args.no_write)
    elif args.command == "starters":
        starting_positions(args.num_lines, write=not args.no_write)
    elif args.command == "plot":
        path = RESULTS / f"{args.num_lines}_lines_scores.txt"
        if not path.exists():
            sys.exit(f"{path} is missing. Run `lines {args.num_lines}` first")
        text = path.read_text()
        scores = ast.literal_eval(text[text.index("[") : text.rindex("]") + 1])
        plot_scores(scores, args.num_lines, out=args.out)
    elif args.command == "demo":
        demo()


if __name__ == "__main__":
    main()
