"""Independent checks on the numbers the README publishes.

    python3 viz/checks.py

Three of them:

1. Recount the 1728000 three-line scores with the standalone scorer in wall.py
   and compare, score by score, with the file the engine produced. This is what
   backs the claim that the histogram's flat top is real and not a bug.

2. Enumerate every way to fill a single column when you have R rounds left, and
   report the best total. This is the "you can only grow a column one tile per
   round" rule, measured rather than argued.

3. Re-derive the openings from the combination files and check that the counts
   add up to the number of maximal and minimal fillings.
"""

from __future__ import annotations

import ast
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import wall as W

RESULTS = Path(__file__).resolve().parent.parent / "results"


def dashes(title):
    print(f"\n{title}\n{'=' * len(title)}")


# ================================================ 1. the shape of the histogram ==

def recount_three_lines():
    dashes("1. recounting the three-line distribution")

    perms = list(itertools.permutations(range(5)))
    mine = {}
    for a in perms:
        for b in perms:
            for c in perms:
                s = W.score_of((a, b, c))
                mine[s] = mine.get(s, 0) + 1

    text = (RESULTS / "3_lines_scores.txt").read_text()
    engine_scores = ast.literal_eval(text[text.index("[") : text.rindex("]") + 1])
    theirs = {}
    for s in engine_scores:
        theirs[s] = theirs.get(s, 0) + 1

    print(f"boards counted: {sum(mine.values())} (engine: {sum(theirs.values())})")
    if mine == theirs:
        print("every bar matches the engine's file exactly")
    else:
        print("MISMATCH:")
        for s in sorted(set(mine) | set(theirs)):
            if mine.get(s) != theirs.get(s):
                print(f"  {s}: standalone {mine.get(s)} vs engine {theirs.get(s)}")

    # the flat top the README asks about
    peak = max(mine.values())
    print("\nthe top of the curve, and why it looks flat:")
    for s in sorted(mine):
        n = mine[s]
        if n > peak * 0.8:
            print(f"  {s} points: {n:>7}  ({n / peak * 100:.1f}% of the tallest bar)")
    top = sorted(mine.items(), key=lambda kv: -kv[1])[:2]
    (s1, n1), (s2, n2) = top
    print(f"\ntallest two bars: {s1} ({n1}) and {s2} ({n2}), "
          f"{abs(n1 - n2)} apart, {abs(n1 - n2) / n1 * 100:.2f}% of the peak")
    print("mean:", round(sum(s * n for s, n in mine.items()) / sum(mine.values()), 3))
    print("\nSo the flat-looking top is real, not a bug. 56 and 57 are a near tie")
    print("(0.44% apart), their neighbours 55 and 58 are already 9% lower, and the")
    print("curve is skewed: mode 56, mean 57.2, and 23 points of range from 47 to 70.")
    print("A sum of five dependent per-round gains has no reason to be a clean bell.")
    return mine == theirs


# ============================================= 2. how fast a column can be built ==

def column_points(order):
    """Points for one column filled in the given per-row rounds, in isolation.

    `order[i]` is the round in which row i is filled. Within a round the wall is
    filled from the top row down, which is the whole point of this check: a tile
    counts the tiles above it that arrived earlier in the same round, but not
    the ones below it that arrive later.
    """
    placed = set()
    total = 0
    for rnd in sorted(set(order)):
        for row in range(len(order)):
            if order[row] != rnd:
                continue
            run = 1
            r = row - 1
            while r >= 0 and r in placed:
                run += 1
                r -= 1
            r = row + 1
            while r < len(order) and r in placed:
                run += 1
                r += 1
            total += run if run > 1 else 1
            placed.add(row)
    return total


def column_budget(height=5):
    dashes("2. filling one column with R rounds left")

    best_possible = height * (height + 1) // 2
    print(f"a column of {height} is worth at most 1+2+...+{height} = {best_possible}\n")
    print(f"{'rounds left':>12} {'best total':>11} {'lost':>6}   an order that gets there")
    for rounds in range(1, height + 1):
        best, witness = -1, None
        for order in itertools.product(range(rounds), repeat=height):
            if len(set(order)) != rounds:      # must actually use every round
                continue
            pts = column_points(order)
            if pts > best:
                best, witness = pts, order
        shown = tuple(r + 1 for r in witness)
        print(f"{rounds:>12} {best:>11} {best_possible - best:>6}   rows get rounds {shown}")

    print("\nSo an empty column costs nothing to fill, however few rounds you have,")
    print("as long as you go top to bottom. Inside one round the wall is filled from")
    print("the top row down, so each tile already has the one above it to lean on.")
    print("Growing a column downwards is free. Growing it upwards is not:")

    dashes("2b. holes above a tile that is already placed")
    print("a tile is already on the wall. N squares above it are empty, R rounds")
    print("remain. Best total for those N tiles:\n")
    print(f"{'holes':>6} {'rounds':>7} {'best':>6} {'one per round':>14}")
    for holes in (1, 2, 3, 4):
        base = holes                      # the existing tile sits below the holes
        for rounds in range(1, holes + 1):
            best = -1
            for order in itertools.product(range(rounds), repeat=holes):
                if len(set(order)) != rounds:
                    continue
                # round 0 is "already there", before any of the holes are filled
                full = [o + 1 for o in order] + [0]
                best = max(best, column_points(full) - 1)   # drop the base tile's own point
            ideal = sum(range(2, holes + 2))
            flag = "yes" if best == ideal else f"no, {ideal - best} short"
            print(f"{holes:>6} {rounds:>7} {best:>6} {flag:>14}")
    print("\nThe loss is exactly N - R every time. Rule of thumb at the table: count")
    print("the empty squares above each tile you have already placed. If there are")
    print("more of them than there are rounds left, the difference is points you")
    print("have already lost.")


# ==================================================== 3. the openings add up ==

def openings_add_up():
    dashes("3. the openings account for every extreme filling")
    import re

    ok = True
    for name, expected in (("best", 230), ("worst", 20)):
        path = RESULTS / f"3_lines_{name}_starters.txt"
        counts = [int(m) for m in re.findall(r"Number of duplicates: (\d+)", path.read_text())]
        total = sum(counts)
        print(f"{name:>6}: {len(counts)} openings, counts sum to {total} "
              f"(expected {expected}) {'ok' if total == expected else 'MISMATCH'}")
        ok &= total == expected

        # every opening should have its left-right mirror, with the same count
        blocks = {}
        for block in path.read_text().split("Number of duplicates: ")[1:]:
            lines = block.strip().splitlines()
            n = int(lines[0])
            grid = tuple(W.parse("\n".join(lines[1:])))
            blocks[grid] = n
        mirrored = all(
            blocks.get(tuple(tuple(reversed(row)) for row in g)) == n
            for g, n in blocks.items()
        )
        print(f"        every opening's mirror image is present with the same count: "
              f"{'yes' if mirrored else 'NO'}")
        ok &= mirrored
    return ok


if __name__ == "__main__":
    a = recount_three_lines()
    column_budget()
    c = openings_add_up()
    sys.exit(0 if (a and c) else 1)
