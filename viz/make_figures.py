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

# The four fillings the README talks about, as per-column round numbers.
CENTRE = (3, 1, 0, 2, 4)          # middle first, then out to both sides
LEFT_TO_RIGHT = (0, 1, 2, 3, 4)

OBVIOUS_3 = (CENTRE,) * 3         # 68
BEST_3 = ((0, 1, 2, 3, 4), (3, 2, 1, 0, 4), (3, 2, 0, 1, 4))   # 70
WORST_3 = ((0, 2, 1, 4, 3), (1, 2, 0, 4, 3), (0, 1, 4, 3, 2))  # 47

BEST_1 = (LEFT_TO_RIGHT,)                     # 15
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


def run_column(label, grid, tag, kind, series, i, rows, *, tile=26,
               show_static=True, static_label="the whole filling",
               live_label="round by round"):
    """One filling: the numbered board, then the same board mid-flight."""
    final, current = series[-1], series[i]
    boards = ""
    if show_static:
        boards += ("<div class='stack' style='gap:6px'>" +
                   P.wall(final, rows=rows, tile=tile) +
                   P.label(static_label) + "</div>")
    boards += ("<div class='stack' style='gap:6px'>" +
               P.wall(current, rows=rows, tile=tile, mark_fresh=True) +
               P.label(live_label) + "</div>")
    return ("<div class='stack' style='gap:10px'>" + P.label(label) +
            f"<div class='strip' style='gap:16px;align-items:flex-start'>{boards}</div>" +
            P.score(current) + (P.verdict(tag, kind) if tag else "") + "</div>")


def comparison(name, heading, sub, runs, rows, *, tile=26, show_static=True,
               gap=28):
    """A GIF comparing two or three fillings, tile by tile."""
    series = [W.steps(grid) for _, grid, _, _ in runs]
    bodies = []
    for i in range(len(series[0])):
        cards = "".join(
            run_column(label, grid, tag, kind, s, i, rows, tile=tile,
                       show_static=show_static)
            for (label, grid, tag, kind), s in zip(runs, series))
        bodies.append(P.shot(P.panel(
            P.title(heading, sub) +
            P.pips(series[0][i].round) +
            "<div style='height:12px'></div>" +
            f"<div class='strip' style='gap:{gap}px'>{cards}</div>")))
    animate(name, bodies, series[0])


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


# ============================================================= 1. the notation ==

@figure("notation")
def notation():
    series = W.steps(OBVIOUS_3)
    bodies = []
    for i, frame in enumerate(series):
        left = ("<div class='stack' style='gap:6px'>" +
                P.wall(series[-1], rows=3, tile=32, row_keys=True) +
                P.label("the whole filling in one picture") + "</div>")
        right = ("<div class='stack' style='gap:6px'>" +
                 P.wall(frame, rows=3, tile=32, mark_fresh=True, row_keys=True) +
                 P.label("the same filling, tile by tile") + "</div>")
        bodies.append(P.shot(P.panel(
            P.title("How to read these boards",
                    "The number on a tile is the round it was placed in. Inside a "
                    "round the wall fills from the top row down, which is why the "
                    "tiles land in that order.") +
            f"<div class='strip' style='gap:34px;align-items:flex-start'>{left}{right}</div>"
            "<div style='height:14px'></div>" +
            P.pips(frame.round) +
            "<div style='height:6px'></div>" +
            P.score(frame), width="820px")))
    animate("notation", bodies, series)
    return []


# ========================================================== 2, 3, 4. the runs ==

@figure("one_line")
def one_line():
    comparison(
        "one_line", "One row, five tiles",
        "Every order lands between 11 and 15 points. The 15s are the orders that "
        "never leave a hole.",
        [("Best: 15 points", BEST_1, "16 of the 120 orders", "best"),
         ("Worst: 11 points", WORST_1, "40 of the 120 orders", "worst")],
        rows=1, tile=32)
    return []


@figure("two_lines")
def two_lines():
    comparison(
        "two_lines", "Two rows, ten tiles",
        "29 to 40 points. Now the columns matter, and the obvious filling is "
        "already one point short.",
        [("The obvious way: 39", OBVIOUS_2, "middle first, then outwards", "mid"),
         ("Best: 40", BEST_2, "186 of 14 400 orders", "best"),
         ("Worst: 29", WORST_2, "256 of 14 400 orders", "worst")],
        rows=2, tile=26)
    return []


@figure("three_lines")
def three_lines():
    comparison(
        "three_lines", "Three rows, fifteen tiles",
        "Same 15 tiles, same 3 rows, only the order changes.",
        [("The obvious way: 68", OBVIOUS_3, "middle first, then outwards", "mid"),
         ("Best: 70", BEST_3, "230 of 1 728 000 orders", "best"),
         ("Worst: 47", WORST_3, "20 of 1 728 000 orders", "worst")],
        rows=3, tile=26)
    return []


# ======================================================== 5. counting a tile ==

@figure("scoring")
def scoring():
    def card(heading, stamps, spot, text):
        placed = dict(stamps)
        pts = W.points_for(set(placed) - {spot}, *spot)
        frame = W.still(placed)
        return ("<div class='stack' style='gap:9px;width:320px'>" +
                P.label(heading) +
                P.wall(frame, rows=3, stamps=False, spots=(spot,)) +
                f"<div class='score'><span class='pts'>{pts}</span>"
                f"<span class='pts-unit'>point{'s' if pts != 1 else ''}</span></div>" +
                P.note(text, "32ch") + "</div>")

    alone = card("nothing next to it", {(1, 2): 0}, (1, 2),
                 "A tile with no neighbour is worth <b>1</b>.")
    line = card("a row of four", {(1, 0): 0, (1, 1): 0, (1, 2): 0, (1, 3): 0}, (1, 3),
                "Closing a horizontal run of four scores the whole run: <b>4</b>.")
    both = card("a row and a column", {(0, 2): 0, (1, 0): 0, (1, 1): 0, (1, 2): 0,
                                       (1, 3): 0, (2, 2): 0}, (1, 2),
                "With neighbours both ways the tile is counted twice, once in the "
                "row of four and once in the column of three: 4 + 3 = <b>7</b>.")

    body = P.shot(P.panel(
        P.title("Why a tile can be worth seven",
                "A tile scores the length of its horizontal run, the length of its "
                "vertical run, or both. The dashed square is the tile that just "
                "landed.") +
        f"<div class='strip' style='gap:24px'>{alone}{line}{both}</div>"))
    return [("scoring.png", body)]


# ================================================== 6. the two kinds of gap ==

@figure("gaps")
def gaps():
    cases = [
        ("All three in one round", ((0,), (0,), (0,)), "good", (),
         "The wall fills from the top row down, so each tile already has the one "
         "above it to lean on. 1 + 2 + 3."),
        ("One per round, downwards", ((0,), (1,), (2,)), "good", (),
         "Same thing spread over three rounds. Each tile lands on the bottom of a "
         "growing column. 1 + 2 + 3."),
        ("Row 2 left for later", ((0,), (1,), (0,)), "bad", ((1, 0),),
         "In round 1 the row-3 tile has nothing above it. It scores 1 instead of 3, "
         "and the column never gets that point back."),
    ]

    def board(frame, text, marks=()):
        return ("<div class='stack' style='gap:5px'>" +
                P.wall(frame, rows=3, gaps=marks, tile=22) + P.label(text) + "</div>")

    cards = []
    for heading, grid, kind, marks, text in cases:
        frames = W.play(grid, rounds=3)
        first = W.play(grid, rounds=1)[-1]
        if first.placed == frames[-1].placed:
            boards = board(first, "after round 1, and finished", marks)
        else:
            boards = board(first, "after round 1", marks) + board(frames[-1], "finished")
        cards.append(
            "<div class='stack' style='gap:10px;width:340px'>" + P.label(heading) +
            f"<div class='strip' style='gap:14px;align-items:flex-end'>{boards}</div>"
            f"<div class='score'><span class='pts'>{frames[-1].score}</span>"
            "<span class='pts-unit'>points</span></div>" +
            P.chips(frames[1:]) +
            f"<div class='callout {kind}'>{text}</div></div>")

    body = P.shot(P.panel(
        P.title("A column grows downwards for free",
                "Three ways to put the same three tiles in the same column. All "
                "three end with an identical wall. The crossed square is the one "
                "left empty, and it costs a point.") +
        f"<div class='strip' style='gap:24px'>{''.join(cards)}</div>"))
    return [("gaps.png", body)]


HOLES = 3   # empty squares above the tile, in the budget figure


def best_column_filling(holes: int, rounds_left: int):
    """Search for the best way to close `holes` squares above a tile.

    The tile sits at row `holes + 1` and went up in round 1. The holes above it
    must be filled during the `rounds_left` rounds that follow. Returns the
    winning grid and its frames, so the figure draws a filling that was found
    rather than one that was assumed.
    """
    import itertools

    best = (-1, None)
    for assignment in itertools.product(range(1, rounds_left + 1), repeat=holes):
        if len(set(assignment)) != rounds_left:     # use every round available
            continue
        grid = tuple((r,) for r in assignment) + ((0,),)
        grid += ((None,),) * (W.SIZE - len(grid))
        score = W.play(grid, rounds=rounds_left + 1)[-1].score
        if score > best[0]:
            best = (score, grid)
    return best[1], W.play(best[1], rounds=rounds_left + 1)


@figure("budget")
def budget():
    ideal = max(W.play(best_column_filling(HOLES, HOLES)[0],
                       rounds=HOLES + 1)[-1].score for _ in (0,))

    cases = []
    for rounds_left in (HOLES, 2, 1):
        grid, frames = best_column_filling(HOLES, rounds_left)
        total = frames[-1].score
        lost = ideal - total
        wasted = max(0, HOLES - rounds_left)
        kind = "good" if lost == 0 else "bad"
        text = (f"One hole per round, bottom up. Every tile lands against the block "
                f"below it and the column is worth all {ideal} points."
                if lost == 0 else
                f"{wasted} of the {HOLES} tiles has to land on top of an empty square, "
                f"where it scores nothing vertically. The column is worth {total} "
                f"instead of {ideal}."
                if wasted == 1 else
                f"{wasted} of the {HOLES} tiles have to land on top of an empty square, "
                f"where they score nothing vertically. The column is worth {total} "
                f"instead of {ideal}.")
        cases.append(
            "<div class='stack' style='gap:9px;width:262px'>" +
            P.label(f"{rounds_left} round{'s' if rounds_left > 1 else ''} to fill them") +
            P.wall(frames[-1], rows=HOLES + 2, live_rows=HOLES + 1, tile=28,
                   row_keys=True) +
            f"<div class='score'><span class='pts'>{total}</span>"
            f"<span class='pts-unit'>points</span>" +
            ("<span class='delta'>nothing lost</span>" if lost == 0 else
             f"<span class='delta loss'>{lost} lost</span>") + "</div>" +
            P.chips(frames[1:]) +
            f"<div class='callout {kind}'>{text}</div></div>")

    body = P.shot(P.panel(
        P.title("Holes above a tile need one round each",
                f"A tile went up in round 1 with {HOLES} empty squares above it. A tile "
                "only counts a vertical neighbour that is already there, and inside a "
                "round the wall fills downwards, so a column can only be extended "
                "upwards one tile per round. With H holes above a tile and R rounds "
                "left, at least H minus R of those tiles are wasted. These are the "
                "best fillings the search can find in each case.") +
        f"<div class='strip' style='gap:24px'>{''.join(cases)}</div>"))
    return [("column_budget.png", body)]


# ============================================================== 7. starters ==

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
            "The ten openings most likely to end at 70",
            "Round 1 puts one tile in each of the top three rows. Of the "
            f"{thousands(best_total)} fillings that reach 70, the number under each "
            f"board is how many start this way. All {len(best)} winning openings are "
            "listed in results/3_lines_best_starters.txt.",
            best[:10], best_total, 5)),
        ("starters_worst.png", sheet(
            "Every opening that can end at 47",
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
         "Both ends of every row are still open."),
        ("Lateral small step", lateral,
         "<b>Row 3</b> is against the edge and has one way to grow. It is the last "
         "row to be filled, so being short of a choice there costs less."),
        ("Diagonal", diagonal,
         "The same number of squares as the lateral step, less than half as many "
         "perfect fillings. Here it is <b>row 1</b> that is short of a choice, and "
         "row 1 goes first."),
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
                "are where round 2 could continue that row without leaving a hole, "
                "and the count on the right is how many of them there are. Read the "
                "three counts downwards: 2·2·2, 2·2·1, 1·2·2.") +
        f"<div class='strip' style='gap:26px'>{''.join(html)}</div>"))
    return [("small_steps.png", body)]


# ============================================================ 8. asymmetry ==

@figure("asymmetry")
def asymmetry():
    inward = ((0, 1, 2, 3, 4), (1, 0, 2, 3, 4), (2, 1, 0, 3, 4))    # 68
    outward = ((0, 1, 2, 3, 4), (2, 0, 1, 3, 4), (2, 1, 0, 3, 4))   # 70
    assert W.score_of(inward) == 68 and W.score_of(outward) == 70

    runs = [("Row 2 grows left: 68", inward, "68 is the ceiling from here", "worst"),
            ("Row 2 grows right: 70", outward, "the maximum", "best")]
    series = [W.steps(grid) for _, grid, _, _ in runs]

    bodies = []
    for i in range(len(series[0])):
        cards = []
        for (label, grid, tag, kind), s in zip(runs, series):
            done = W.play(grid)
            cards.append(
                "<div class='stack' style='gap:10px;width:330px'>" + P.label(label) +
                P.wall(s[i], rows=3, tile=30, mark_fresh=True, row_keys=True) +
                P.score(s[i]) + P.chips(done[1:], highlight=2) +
                P.verdict(tag, kind) + "</div>")
        bodies.append(P.shot(P.panel(
            P.title("Rows are not interchangeable",
                    "Both boards open with the same diagonal in round 1 and differ by "
                    "one tile in round 2. Watch round 3: on the left, the row-1 tile "
                    "of column 3 lands before the row-2 tile below it and cannot count "
                    "it. That is the whole 2 point difference.") +
            P.pips(series[0][i].round) +
            "<div style='height:12px'></div>" +
            f"<div class='strip' style='gap:30px'>{''.join(cards)}</div>")))
    animate("asymmetry", bodies, series[0])
    return []


# ============================================================ 9. histograms ==

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
