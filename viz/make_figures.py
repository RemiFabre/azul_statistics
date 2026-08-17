"""Draw every picture the README shows.

    python3 viz/make_figures.py             # everything, a few minutes
    python3 viz/make_figures.py one_line    # just the figures whose name matches
    python3 viz/make_figures.py --list      # what there is

Figures land in ``images/`` and the histograms in ``results/``. Every number
printed on a figure is computed here from the same scoring rules the analysis
used (``viz/wall.py``, cross-checked against ``src/board.py`` by
``viz/test_wall.py``). Nothing is typed in by hand.

Rows, columns and rounds read 1 to 5, not 0 to 4.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import parts as P
import render
import wall as W

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "images"
RESULTS = ROOT / "results"
BUILD = Path(__file__).resolve().parent / "build"

# The fillings the README talks about, as per-column round numbers (0-based).
CENTRE = (3, 1, 0, 2, 4)          # middle first, then out to both sides

OBVIOUS_3 = (CENTRE,) * 3         # 68
BEST_3 = ((0, 1, 2, 3, 4), (3, 2, 1, 0, 4), (3, 2, 0, 1, 4))   # 70
WORST_3 = ((0, 2, 1, 4, 3), (1, 2, 0, 4, 3), (0, 1, 4, 3, 2))  # 47

BEST_1 = ((0, 1, 2, 3, 4),)                   # 15
WORST_1 = ((0, 1, 4, 2, 3),)                  # 11
OBVIOUS_2 = (CENTRE,) * 2                     # 39
BEST_2 = ((0, 1, 2, 3, 4), (1, 0, 2, 3, 4))   # 40
WORST_2 = ((0, 2, 1, 4, 3), (0, 2, 1, 4, 3))  # 29

FIGURES = {}


def figure(name):
    def wrap(fn):
        FIGURES[name] = fn
        return fn
    return wrap


# =============================================================== the results ==

def read_starters(path: Path):
    out, count, rows = [], None, []
    for line in path.read_text().splitlines():
        m = re.match(r"Number of duplicates: (\d+)", line)
        if m:
            if count is not None and rows:
                out.append((count, tuple(rows)))
            count, rows = int(m.group(1)), []
        elif line.startswith("("):
            rows.append(W.parse(line)[0])
    if count is not None and rows:
        out.append((count, tuple(rows)))
    return out


def read_scores(path: Path):
    text = path.read_text()
    body = text[text.index("["):text.rindex("]") + 1]
    counts = {}
    for s in ast.literal_eval(body):
        counts[s] = counts.get(s, 0) + 1
    return counts


def thousands(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def ways(lines: int):
    """{score: how many orders end there} and the total, for `lines` rows."""
    counts = read_scores(RESULTS / f"{lines}_lines_scores.txt")
    return counts, sum(counts.values())


# ================================================================ animation ==

def holds(frames, *, tile=2, round_end=7, first=4, last=26):
    """How long each frame stays up, in ticks of 1/fps.

    A short beat between tiles, a longer one at the end of a round so the
    round's total can be read, and a long hold on the finished board.
    """
    out = []
    for i, f in enumerate(frames):
        if i == 0:
            out.append(first)
        elif i == len(frames) - 1:
            out.append(last)
        elif f.closes_round:
            out.append(round_end)
        else:
            out.append(tile)
    return out


def animate(name, bodies, reference, fps=10):
    """Render a list of bodies as one GIF in images/."""
    frames = render.shoot_series(bodies, BUILD / name, name)
    render.gif(frames, IMAGES / f"{name}.gif", holds(reference), fps=fps)
    print(f"images/{name}.gif  {len(bodies)} frames")


def comparison(name, heading, sub, runs, rows, *, tile=32, gap=30,
               rounds_shown=W.SIZE, show_pips=True, ref=0):
    """A GIF comparing fillings side by side, one landing tile per frame.

    Each run is (title, grid, count_pill_or_None, kind). The title carries the
    final score and is drawn big, in the colour of its verdict.
    """
    series = [W.steps(grid) for _, grid, _, _ in runs]
    n = len(series[0])
    assert all(len(s) == n for s in series), "runs must land the same tile count"

    bodies = []
    for i in range(n):
        cards = []
        for (title, grid, tag, kind), s in zip(runs, series):
            cards.append(
                "<div class='stack' style='gap:9px'>"
                f"<div class='runhead {kind}'>{title}</div>" +
                P.wall(s[i], rows=rows, tile=tile, mark_fresh=True) +
                P.score(s[i]) +
                (P.verdict(tag, kind) if tag else "") +
                "</div>")
        top = ""
        if show_pips:
            top = (P.pips(series[0][i].round, rounds_shown) +
                   "<div style='height:12px'></div>")
        bodies.append(P.shot(P.panel(
            P.title(heading, sub) + top +
            f"<div class='strip' style='gap:{gap}px'>{''.join(cards)}</div>")))
    animate(name, bodies, series[ref])


# ============================================================= the notation ==

@figure("notation")
def notation():
    series = W.steps(OBVIOUS_3)
    bridge = ("<div class='same'><span class='arrow'>&#x21C4;</span>" +
              P.label("same thing") + "</div>")
    bodies = []
    for frame in series:
        left = ("<div class='stack' style='gap:6px'>" +
                P.wall(series[-1], rows=3, tile=32, row_keys=True) +
                P.label("the whole filling in one picture") + "</div>")
        right = ("<div class='stack' style='gap:6px'>" +
                 P.wall(frame, rows=3, tile=32, mark_fresh=True, row_keys=True) +
                 P.label("the same filling, tile by tile") + "</div>")
        bodies.append(P.shot(P.panel(
            P.title("How to read these boards",
                    "The number on a tile is the round it was placed in. Inside a "
                    "round the wall fills from the top row down.") +
            f"<div class='strip' style='gap:22px;align-items:center'>{left}{bridge}{right}</div>"
            "<div style='height:14px'></div>" +
            P.pips(frame.round) +
            "<div style='height:6px'></div>" +
            P.score(frame), width="880px")))
    animate("notation", bodies, series)
    return []


# ============================================================ the three runs ==

@figure("one_line")
def one_line():
    counts, total = ways(1)
    comparison(
        "one_line", "One row, five tiles",
        f"There are {total} ways to tile one row. They score between 11 and 15.",
        [("The best way: 15", BEST_1,
          f"{counts[15]} of {total} orders", "best"),
         ("The worst way: 11", WORST_1,
          f"{counts[11]} of {total} orders", "worst")],
        rows=1, tile=38, gap=44)
    return []


@figure("two_lines")
def two_lines():
    counts, total = ways(2)
    comparison(
        "two_lines", "Two rows, ten tiles",
        "Now the columns matter.",
        [("The obvious way: 39", OBVIOUS_2,
          f"{counts[39]} of {thousands(total)} orders", "mid"),
         ("The best way: 40", BEST_2,
          f"{counts[40]} of {thousands(total)} orders", "best"),
         ("The worst way: 29", WORST_2,
          f"{counts[29]} of {thousands(total)} orders", "worst")],
        rows=2, tile=32)
    return []


@figure("three_lines")
def three_lines():
    counts, total = ways(3)
    comparison(
        "three_lines", "Three rows, fifteen tiles",
        "Same 15 tiles, same 3 rows, only the order changes.",
        [("The obvious way: 68", OBVIOUS_3,
          f"{thousands(counts[68])} of {thousands(total)} orders", "mid"),
         ("The best way: 70", BEST_3,
          f"only {counts[70]} of {thousands(total)} orders", "best"),
         ("The worst way: 47", WORST_3,
          f"only {counts[47]} of {thousands(total)} orders", "worst")],
        rows=3, tile=32)
    return []


# ========================================================== the double count ==

@figure("double_count")
def double_count():
    obvious = ((0, 1, None, None, None), (0, 1, None, None, None))
    weird = ((0, 1, None, None, None), (1, 0, None, None, None))
    assert W.score_of(obvious) == 9 and W.score_of(weird) == 10

    comparison(
        "double_count", "The smallest example: a 2x2 block",
        "Two rounds, two tiles per round, same four tiles.",
        [("The obvious way: 9", obvious, "column by column", "mid"),
         ("The weird way: 10", weird, "diagonal first", "best")],
        rows=2, tile=38, gap=44, rounds_shown=2)
    return []


# ======================================================== the two kinds of gap ==

@figure("gaps")
def gaps():
    down = ((0,), (0,), (0,))       # 6: all three in one round, top to bottom
    up_slow = ((2,), (1,), (0,))    # 6: upwards, one per round
    up_fast = ((1,), (1,), (0,))    # 5: upwards, two in one round
    assert W.score_of(down) == 6 and W.score_of(up_slow) == 6
    assert W.score_of(up_fast) == 5

    comparison(
        "gaps", "Growing a column",
        "Same three tiles, same column, three orders.",
        [("Downwards, all at once: 6", down, "no mistake", "best"),
         ("Upwards, one per round: 6", up_slow, "no mistake", "best"),
         ("Upwards, two in one round: 5", up_fast, "one point lost", "worst")],
        rows=3, tile=32, show_pips=False, ref=1)
    return []


# =============================================== holes above a tile, marked ==

@figure("budget")
def budget():
    frame = W.still({(2, 1): 0}, fresh=((2, 1),))
    notes = ["needs its own round", "needs its own round", "just placed", "", ""]
    body = P.shot(P.panel(
        P.title("Holes above a tile need one round each",
                "This tile was just placed on row 3. The two squares above it can "
                "now be filled at most one per round.") +
        P.wall(frame, rows=5, stamps=False, spots=((0, 1), (1, 1)),
               mark_fresh=True, tile=34, row_keys=True, row_notes=notes)))
    return [("column_budget.png", body)]


# ================================================= the position after round 2 ==

INWARD = ((0, 1, 2, 3, 4), (1, 0, 2, 3, 4), (2, 1, 0, 3, 4))    # 68
OUTWARD = ((0, 1, 2, 3, 4), (2, 0, 1, 3, 4), (2, 1, 0, 3, 4))   # 70


@figure("forced")
def forced():
    assert W.score_of(INWARD) == 68 and W.score_of(OUTWARD) == 70
    left = W.play(INWARD, rounds=2)[-1]
    right = W.play(OUTWARD, rounds=2)[-1]

    lcard = ("<div class='stack' style='gap:9px;width:370px'>"
             "<div class='runhead worst'>Heading for 68</div>" +
             P.wall(left, rows=3, tile=32, spots=((0, 2),), gaps=((1, 2),),
                    row_keys=True) +
             P.note("Row 1 must continue on the dashed square, anything else "
                    "leaves a lateral gap. But column 3 already has a tile on row "
                    "3, so the two squares above it need one round each, and the "
                    "crossed one is still empty. In round 3 the row-1 tile lands "
                    "alone and counts once.", "42ch") +
             "</div>")
    rcard = ("<div class='stack' style='gap:9px;width:370px'>"
             "<div class='runhead best'>Heading for 70</div>" +
             P.wall(right, rows=3, tile=32, spots=((0, 2),), row_keys=True) +
             P.note("One tile differs: row 2 went right in round 2. The square "
                    "below the dashed one is already filled, so in round 3 the "
                    "row-1 tile lands with a row and a column neighbour and "
                    "counts double.", "42ch") +
             "</div>")

    body = P.shot(P.panel(
        P.title("The same position, one tile apart",
                "Both boards opened with the same diagonal. This is the end of "
                "round 2.") +
        f"<div class='strip' style='gap:34px'>{lcard}{rcard}</div>"))
    return [("forced.png", body)]


@figure("asymmetry")
def asymmetry():
    runs = [("Row 2 grows left: 68", INWARD, "68 is the ceiling from here", "worst"),
            ("Row 2 grows right: 70", OUTWARD, "the maximum", "best")]
    series = [W.steps(grid) for _, grid, _, _ in runs]

    bodies = []
    for i in range(len(series[0])):
        cards = []
        for (title, grid, tag, kind), s in zip(runs, series):
            done = W.play(grid)
            cards.append(
                "<div class='stack' style='gap:10px;width:330px'>"
                f"<div class='runhead {kind}'>{title}</div>" +
                P.wall(s[i], rows=3, tile=32, mark_fresh=True, row_keys=True) +
                P.score(s[i]) + P.chips(done[1:], highlight=2) +
                P.verdict(tag, kind) + "</div>")
        bodies.append(P.shot(P.panel(
            P.title("Rows are not interchangeable",
                    "Both boards open with the same diagonal in round 1 and differ "
                    "by one tile in round 2. The whole difference lands in round 3.") +
            P.pips(series[0][i].round) +
            "<div style='height:12px'></div>" +
            f"<div class='strip' style='gap:30px'>{''.join(cards)}</div>")))
    animate("asymmetry", bodies, series[0])
    return []


# ================================================================= starters ==

def starter_grid(count: int, total: int, grid, *, extra="", spots=(), tile=28) -> str:
    frame = W.play(grid, rounds=1)[-1]
    share = min(100, round(100 * count / total))
    return (
        "<div class='stack' style='gap:8px;width:max-content'>" +
        P.wall(frame, rows=3, spots=spots, stamps=False, tile=tile) +
        f"<div class='count'><span class='n'>{count}</span>"
        f"<span class='of'>of {thousands(total)}</span></div>"
        f"<div class='share'><i style='width:{share}%'></i></div>" +
        (P.note(extra, "20ch") if extra else "") + "</div>")


@figure("starters")
def starters():
    best = read_starters(RESULTS / "3_lines_best_starters.txt")
    worst = read_starters(RESULTS / "3_lines_worst_starters.txt")
    best_total = sum(c for c, _ in best)
    worst_total = sum(c for c, _ in worst)

    def sheet(heading, sub, rows, total, per_row):
        cards = "".join(starter_grid(c, total, g) for c, g in rows)
        width = per_row * 190 + (per_row - 1) * 22
        return P.shot(P.panel(
            P.title(heading, sub) +
            f"<div class='strip wrap' style='gap:22px;max-width:{width}px'>{cards}</div>"))

    return [
        ("starters_best.png", sheet(
            "The 10 openings most likely to end at 70 "
            "(the best possible score with three rows)",
            "Round 1 puts one tile in each of the top three rows. Of the "
            f"{thousands(best_total)} fillings that reach 70, the number under each "
            f"board is how many start this way. All {len(best)} winning openings are "
            "listed in results/3_lines_best_starters.txt.",
            best[:10], best_total, 5)),
        ("starters_worst.png", sheet(
            "Every opening that can end at 47 "
            "(the worst possible score with three rows)",
            f"Only {len(worst)} openings can lead to 47 points, and only "
            f"{thousands(worst_total)} of the {thousands(1728000)} fillings get there. "
            "The two most likely ones put a tile in row 1 and a tile in row 3 in the "
            "same column, leaving row 2 empty.",
            worst, worst_total, 6)),
    ]


@figure("bothsets")
def bothsets():
    best = {g: c for c, g in read_starters(RESULTS / "3_lines_best_starters.txt")}
    worst = {g: c for c, g in read_starters(RESULTS / "3_lines_worst_starters.txt")}
    best_total, worst_total = sum(best.values()), sum(worst.values())

    cards = []
    for g in sorted((g for g in best if g in worst), key=lambda g: -best[g]):
        cards.append(
            "<div class='stack' style='gap:8px;width:max-content'>" +
            P.wall(W.play(g, rounds=1)[-1], rows=3, stamps=False) +
            "<div class='strip' style='gap:10px'>" +
            P.verdict(f"{best[g]} of {best_total} best", "best") +
            P.verdict(f"{worst[g]} of {worst_total} worst", "worst") +
            "</div></div>")

    body = P.shot(P.panel(
        P.title("The large steps, in both lists",
                "These two openings, and only these two, appear both among the starts "
                "that can reach 70 and among the starts that can end at 47. Each step "
                "goes down one row and across two columns.") +
        f"<div class='strip' style='gap:26px'>{''.join(cards)}</div>"))
    return [("large_steps.png", body)]


@figure("steps")
def steps():
    best = {g: c for c, g in read_starters(RESULTS / "3_lines_best_starters.txt")}
    total = sum(best.values())

    central = ((None, 0, None, None, None), (None, None, 0, None, None),
               (None, None, None, 0, None))
    lateral = ((None, None, 0, None, None), (None, None, None, 0, None),
               (None, None, None, None, 0))
    diagonal = ((0, None, None, None, None), (None, 0, None, None, None),
                (None, None, 0, None, None))

    def neighbours(grid):
        per_row = []
        for row in grid:
            col = next(c for c, v in enumerate(row) if v == 0)
            per_row.append([(len(per_row), c) for c in (col - 1, col + 1)
                            if 0 <= c < W.SIZE])
        return per_row

    cards = [
        ("Central small step", central,
         "Both ends of every row are open: two optimal placements per row."),
        ("Lateral small step", lateral,
         "Row 3 is against the edge and has one optimal placement. Roughly twice "
         "as hard to optimize."),
        ("Diagonal", diagonal,
         "Six open squares, same as the central step, yet the fewest perfect "
         "fillings. The trap is a forced vertical gap, shown below."),
    ]

    html = []
    for heading, grid, text in cards:
        per_row = neighbours(grid)
        spots = tuple(s for row in per_row for s in row)
        notes = [f"{len(row)} way{'s' if len(row) != 1 else ''}" for row in per_row]
        count = best.get(grid, 0)
        share = round(100 * count / total)
        html.append(
            "<div class='stack' style='gap:9px;width:315px'>" + P.label(heading) +
            P.wall(W.play(grid, rounds=1)[-1], rows=3, stamps=False, spots=spots,
                   tile=28, row_notes=notes) +
            f"<div class='count'><span class='n'>{count}</span>"
            f"<span class='of'>of {thousands(total)} perfect fillings</span></div>"
            f"<div class='share' style='width:220px'><i style='width:{share}%'></i></div>" +
            P.note(text, "34ch") + "</div>")

    body = P.shot(P.panel(
        P.title("One step at a time, and where it can go next",
                "Three staircase openings, top three rows only. The dashed squares "
                "are where round 2 can continue each row without a lateral gap.") +
        f"<div class='strip' style='gap:26px'>{''.join(html)}</div>"))
    return [("small_steps.png", body)]


# =============================================================== histograms ==

def histogram(counts: dict, lines: int) -> str:
    lo, hi = min(counts), max(counts)
    peak = max(counts.values())
    total = sum(counts.values())

    bins = []
    for s in range(lo, hi + 1):
        n = counts.get(s, 0)
        kind = " edge-min" if s == lo else (" edge-max" if s == hi else "")
        tag = thousands(n) if kind else ""
        bins.append(f"<div class='bin{kind}'><span class='v'>{tag}</span>"
                    f"<div class='bar' style='height:{100 * n / peak:.3f}%'></div>"
                    f"<span class='x'>{s}</span></div>")

    axis = ("<div class='axis-y'>"
            f"<span>{thousands(peak)}</span><span>{thousands(peak // 2)}</span>"
            "<span>0</span></div>")

    word = "row" if lines == 1 else "rows"
    return P.shot(P.panel(
        P.title(f"Every way to fill {lines} {word}",
                f"All {thousands(total)} orders in which the top {lines} {word} of the "
                f"wall can be filled, counted by the score they end on. Worst {lo} "
                f"({thousands(counts[lo])} ways), best {hi} "
                f"({thousands(counts[hi])} ways).") +
        f"<div class='strip' style='gap:0'>{axis}<div class='hist'>{''.join(bins)}</div></div>"
        "<div style='height:8px'></div>" + P.label("final score")))


@figure("histograms")
def histograms():
    out = []
    for lines in (1, 2, 3):
        counts = read_scores(RESULTS / f"{lines}_lines_scores.txt")
        out.append((RESULTS / f"{lines}_lines.png", histogram(counts, lines)))
    return out


# ==================================================================== driver ==

def main(argv):
    if "--list" in argv:
        print("\n".join(sorted(FIGURES)))
        return
    wanted = argv or list(FIGURES)
    unknown = [w for w in wanted if w not in FIGURES]
    if unknown:
        raise SystemExit(f"unknown figure(s) {unknown}; pick from {sorted(FIGURES)}")

    for name in wanted:
        for target, body in FIGURES[name]():
            path = target if isinstance(target, Path) else IMAGES / target
            size = render.shoot(body, path)
            print(f"{path.relative_to(ROOT)}  {size[0]}x{size[1]}")


if __name__ == "__main__":
    main(sys.argv[1:])
