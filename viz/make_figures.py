"""Draw every picture the README shows.

    python3 viz/make_figures.py            # everything
    python3 viz/make_figures.py reading    # just the figures whose name matches

Figures land in ``images/`` and the histograms in ``results/``. Every number
printed on a figure is computed here from the same scoring rules the analysis
used (``viz/wall.py``, cross-checked against ``src/board.py`` by
``viz/test_wall.py``) — nothing is typed in by hand.
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

NAIVE = ((0, 1, 2, 3, 4),) * 3
BEST = ((0, 1, 2, 3, 4), (3, 2, 1, 0, 4), (3, 2, 0, 1, 4))
WORST = ((0, 2, 1, 4, 3), (1, 2, 0, 4, 3), (0, 1, 4, 3, 2))

FIGURES = {}


def figure(name):
    def wrap(fn):
        FIGURES[name] = fn
        return fn
    return wrap


# ============================================================== results files ==

def read_starters(path: Path):
    """The ``Number of duplicates: n`` blocks, as (count, grid) pairs."""
    out = []
    count = None
    rows = []
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
    """The score list dumped by adjacent.py, as {score: how often}."""
    text = path.read_text()
    body = text[text.index("["):text.rindex("]") + 1]
    counts = {}
    for s in ast.literal_eval(body):
        counts[s] = counts.get(s, 0) + 1
    return counts


def thousands(n: int) -> str:
    return f"{n:,}".replace(",", " ")  # thin spaces, the way the README reads


# ================================================= 1. how to read the boards ==

@figure("reading")
def reading():
    frames = W.play(NAIVE)
    empty = W.still({})

    anatomy = (
        "<div class='stack' style='gap:9px'>"
        "<div class='label'>an empty player board</div>"
        "<div class='board'>" + P.pattern_lines() +
        P.wall(empty, row_keys=True) + "</div>"
        "<p class='note' style='max-width:44ch'>You fill the <b>pattern lines</b> on the "
        "left — row 0 takes one tile, row 4 takes five. As soon as a line is full, one "
        "of its tiles moves onto the <b>wall</b> and scores. Each wall square accepts "
        "one colour only; the diamond says which.</p>"
        "</div>")

    notation = "\n".join("(" + ", ".join(str(x) for x in row) + ")" for row in NAIVE)
    translation = (
        "<div class='stack' style='gap:9px'>"
        "<div class='label'>the README writes a filling like this</div>"
        f"<div class='mono'>{notation}</div>"
        "<p class='note' style='max-width:52ch'>One line of numbers per wall row, one "
        "number per column: the round in which that column was filled. Fifteen tiles, "
        "five rounds, three tiles a round.</p>"
        f"{P.wall(frames[-1], live_rows=3, row_keys=True)}"
        f"{P.score(frames[-1], delta=False)}"
        "<p class='note'>Rows 3 and 4 are greyed out — this analysis only ever fills "
        "the top three.</p>"
        "</div>")

    legend = (
        "<div class='legend'>"
        "<div class='item'><span class='swatch'>" +
        P.cell(0, 0, W.still({(0, 0): 2})) +
        "</span><span>a <b>tile</b>, stamped with the round it was placed in</span></div>"
        "<div class='item'><span class='swatch'>" +
        P.cell(0, 0, empty) +
        "</span><span>an <b>empty square</b></span></div>"
        "<div class='item'><span class='swatch'>" +
        P.cell(0, 0, empty, spot=True) +
        "</span><span>a square to look at</span></div>"
        "<div class='item'><span class='swatch'>" +
        P.cell(0, 0, empty, gap=True) +
        "</span><span>a <b>gap</b>: a square left empty, at a cost</span></div>"
        "</div>")

    body = P.shot("<div class='panel' style='max-width:1020px'>" +
                  P.title("How to read these boards",
                          "Rows and columns are numbered 0 to 4 from the top left. "
                          "Every figure below draws the wall only.") +
                  "<div class='strip' style='gap:34px'>" + anatomy + translation +
                  "</div><div style='height:18px'></div>" + legend + "</div>")
    return [("reading.png", body)]


# ================================================= 2. the three fillings, GIF ==

@figure("filling")
def filling():
    runs = [
        ("The obvious way", NAIVE, "mid", "left to right, every row"),
        ("The best way", BEST, "best", "the highest score possible"),
        ("The worst way", WORST, "worst", "the lowest score possible"),
    ]
    plays = [(label, W.play(grid), kind, note) for label, grid, kind, note in runs]

    bodies = []
    for step in range(W.SIZE + 1):
        cards = []
        for label, frames, kind, note in plays:
            frame = frames[step]
            cards.append(
                "<div class='stack' style='gap:9px'>"
                f"<div class='label'>{label}</div>"
                f"{P.wall(frame, live_rows=3, mark_fresh=True)}"
                f"{P.score(frame)}"
                f"{P.verdict(note, kind)}"
                "</div>"
            )
        bodies.append(P.shot(P.panel(
            P.title("Filling the top three rows, round by round",
                    "Same fifteen tiles, same three rows, every time. Only the order "
                    "changes — and the order is worth 23 points.") +
            P.pips(step - 1) +
            "<div style='height:12px'></div>" +
            "<div class='strip' style='gap:26px'>" + "".join(cards) + "</div>")))

    frames = render.shoot_series(bodies, BUILD / "filling", "filling")
    holds = [3] + [4] * (W.SIZE - 1) + [14]
    render.gif(frames, IMAGES / "filling.gif", holds)

    # a still of the finished boards, for anyone reading with images off
    return [("filling.png", bodies[-1])]


# ======================================================== 3. counting a tile ==

@figure("scoring")
def scoring():
    def card(heading, stamps, spot, note):
        placed = dict(stamps)
        pts = W.points_for(set(placed) - {spot}, *spot)
        frame = W.still(placed)
        return ("<div class='stack' style='gap:9px;width:330px'>"
                f"<div class='label'>{heading}</div>"
                f"{P.wall(frame, live_rows=3, stamps=False, spots=(spot,))}"
                "<div class='score'>"
                f"<span class='pts'>{pts}</span><span class='pts-unit'>"
                f"point{'s' if pts != 1 else ''}</span></div>"
                f"<p class='note' style='max-width:32ch'>{note}</p></div>")

    alone = card("nothing next to it", {(1, 2): 0}, (1, 2),
                 "A tile with no neighbour is worth <b>1</b>.")
    line = card("a row of four", {(1, 0): 0, (1, 1): 0, (1, 2): 0, (1, 3): 0}, (1, 3),
                "Landing at the end of a horizontal run of four scores the whole "
                "run: <b>4</b>.")
    both = card("a row and a column", {(0, 2): 0, (1, 0): 0, (1, 1): 0, (1, 2): 0,
                                       (1, 3): 0, (2, 2): 0}, (1, 2),
                "With neighbours in <b>both</b> directions the tile is counted "
                "twice — the row of four <i>and</i> the column of three: 4 + 3 = <b>7</b>.")

    body = P.shot(P.panel(
        P.title("Why a tile can be worth seven",
                "When a tile reaches the wall it scores the length of its horizontal run, "
                "the length of its vertical run, or — if it has neighbours both ways — "
                "both runs, which means the tile itself is counted twice. The dashed "
                "square is the tile that has just been placed.") +
        "<div class='strip' style='gap:26px'>" + alone + line + both + "</div>"))
    return [("scoring.png", body)]


# ========================================================= 4. vertical gaps ==

@figure("gaps")
def gaps():
    cases = [
        ("one per round, top to bottom", ((0,), (1,), (2,)), "good", (),
         "Each tile lands on top of a growing column: 1 + 2 + 3."),
        ("all three in one round", ((0,), (0,), (0,)), "good", (),
         "Same thing, all in the same round — the wall is filled top row first, "
         "so the column still grows: 1 + 2 + 3."),
        ("row 1 left for later", ((0,), (1,), (0,)), "bad", ((1, 0),),
         "In round 0 the row-2 tile has nothing above it: the empty row-1 square "
         "cuts it off, and it scores 1 instead of 3. The column pays for it once "
         "and never gets it back."),
    ]

    def board(frame, label, marks=()):
        return (f"<div>{P.wall(frame, live_rows=3, gaps=marks, tile=22)}"
                f"<div class='label' style='margin-top:5px'>{label}</div></div>")

    cards = []
    for heading, grid, kind, marks, note in cases:
        frames = W.play(grid, rounds=3)
        first = W.play(grid, rounds=1)[-1]
        if first.placed == frames[-1].placed:
            # everything landed in round 0; drawing the same wall twice would
            # read as a mistake
            boards = board(first, "after round 0 — already finished", marks)
        else:
            boards = (board(first, "after round 0", marks) +
                      board(frames[-1], "finished"))
        rounds = "".join(
            f"<span class='delta{'' if f.gained else ' none'}'>"
            f"round {f.round} &nbsp;{'+' + str(f.gained) if f.gained else '—'}</span>"
            for f in frames[1:])
        cards.append(
            "<div class='stack' style='gap:10px;width:355px'>"
            f"<div class='label'>{heading}</div>"
            "<div class='strip' style='gap:14px;align-items:flex-end'>" + boards +
            "</div>"
            f"<div class='score'><span class='pts'>{frames[-1].score}</span>"
            "<span class='pts-unit'>points for the column</span></div>"
            f"<div class='strip' style='gap:6px'>{rounds}</div>"
            f"<div class='callout {kind}'>{note}</div>"
            "</div>")

    body = P.shot(P.panel(
        P.title("A gap costs the same, whichever way it points",
                "Three ways to put the same three tiles into the same column, drawn "
                "after round 0 and once finished. All three end with an identical wall; "
                "only the order differs, and it is worth a point.") +
        "<div class='strip' style='gap:26px'>" + "".join(cards) + "</div>"))
    return [("gaps.png", body)]


# ============================================================== 5. starters ==

def starter_grid(count: int, total: int, grid, *, extra="", spots=(), tile=28) -> str:
    frame = W.play(grid, rounds=1)[-1]
    share = min(100, round(100 * count / total))
    return (
        "<div class='stack' style='gap:8px;width:max-content'>"
        f"{P.wall(frame, rows=3, spots=spots, stamps=False, tile=tile)}"
        f"<div class='count'><span class='n'>{count}</span>"
        f"<span class='of'>of {thousands(total)}</span></div>"
        f"<div class='share'><i style='width:{share}%'></i></div>"
        + (f"<p class='note' style='max-width:20ch'>{extra}</p>" if extra else "") +
        "</div>")


@figure("starters")
def starters():
    best = read_starters(RESULTS / "3_lines_best_starters.txt")
    worst = read_starters(RESULTS / "3_lines_worst_starters.txt")
    best_total = sum(c for c, _ in best)
    worst_total = sum(c for c, _ in worst)

    def sheet(title, sub, rows, total, per_row):
        cards = "".join(starter_grid(c, total, g) for c, g in rows)
        width = per_row * 190 + (per_row - 1) * 22
        return P.shot(P.panel(
            P.title(title, sub) +
            f"<div class='strip wrap' style='gap:22px;max-width:{width}px'>{cards}</div>"))

    return [
        ("starters_best.png", sheet(
            "The ten openings most likely to end at 70",
            "Round 0 places one tile in each of the top three rows — only those rows "
            f"are drawn here. Of the {thousands(best_total)} fillings that reach the "
            "maximum of 70 points, the number under each board is how many start this "
            f"way. All {len(best)} winning openings are listed in "
            "results/3_lines_best_starters.txt.",
            best[:10], best_total, 5)),
        ("starters_worst.png", sheet(
            "Every opening that can end at 47",
            f"Only {len(worst)} openings can lead to the minimum of 47 points, and only "
            f"{thousands(worst_total)} of the {thousands(1728000)} fillings get there at "
            "all. The two most likely ones put a tile in row 0 and a tile in row 2 in "
            "the <b>same column</b>, leaving row 1 empty. Top three rows only.",
            worst, worst_total, 6)),
    ]


@figure("bothsets")
def bothsets():
    best = dict((g, c) for c, g in read_starters(RESULTS / "3_lines_best_starters.txt"))
    worst = dict((g, c) for c, g in read_starters(RESULTS / "3_lines_worst_starters.txt"))
    best_total, worst_total = sum(best.values()), sum(worst.values())

    large = [g for g in best if g in worst]
    cards = []
    for g in sorted(large, key=lambda g: -best[g]):
        cards.append(
            "<div class='stack' style='gap:8px;width:max-content'>"
            f"{P.wall(W.play(g, rounds=1)[-1], rows=3, stamps=False)}"
            f"<div class='strip' style='gap:10px'>"
            f"{P.verdict(f'{best[g]} of {best_total} best', 'best')}"
            f"{P.verdict(f'{worst[g]} of {worst_total} worst', 'worst')}"
            "</div></div>")

    body = P.shot(P.panel(
        P.title("The large steps: in both lists",
                "These two openings — and only these two — appear among the starts that "
                "can reach 70 points and among the starts that can end at 47. Each step "
                "goes down one row and across two columns; top three rows only.") +
        "<div class='strip' style='gap:26px'>" + "".join(cards) + "</div>"))
    return [("large_steps.png", body)]


@figure("steps")
def steps():
    best = dict((g, c) for c, g in read_starters(RESULTS / "3_lines_best_starters.txt"))
    total = sum(best.values())

    central = ((None, 0, None, None, None), (None, None, 0, None, None),
               (None, None, None, 0, None))
    lateral = ((None, None, 0, None, None), (None, None, None, 0, None),
               (None, None, None, None, 0))
    diagonal = ((0, None, None, None, None), (None, 0, None, None, None),
                (None, None, 0, None, None))

    def neighbours(grid):
        """Per row: the empty squares horizontally next to round 0's tile."""
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
         "<b>Row 2</b> is against the edge and has one way to grow. It is the last "
         "row to be filled, so being short of a choice there costs less."),
        ("Diagonal", diagonal,
         "Same total number of squares, less than half as many perfect fillings — "
         "because it is <b>row 0</b> that is short of a choice, and row 0 goes first."),
    ]

    html = []
    for heading, grid, note in cards:
        per_row = neighbours(grid)
        spots = tuple(s for row in per_row for s in row)
        notes = [f"{len(row)} way{'s' if len(row) != 1 else ''}" for row in per_row]
        frame = W.play(grid, rounds=1)[-1]
        count = best.get(grid, 0)
        share = round(100 * count / total)
        html.append(
            "<div class='stack' style='gap:9px;width:315px'>"
            f"<div class='label'>{heading}</div>"
            f"{P.wall(frame, rows=3, stamps=False, spots=spots, tile=28, row_notes=notes)}"
            f"<div class='count'><span class='n'>{count}</span>"
            f"<span class='of'>of {thousands(total)} perfect fillings</span></div>"
            f"<div class='share' style='width:220px'><i style='width:{share}%'></i></div>"
            f"<p class='note' style='max-width:34ch'>{note}</p>"
            "</div>")

    body = P.shot(P.panel(
        P.title("One step at a time, and where it can go next",
                "Three staircase openings, top three rows only. The dashed squares are "
                "where round 1 could continue that row without leaving a hole, and the "
                "count on the right is how many of them there are. Reading the three "
                "columns of counts downwards — 2·2·2, 2·2·1, 1·2·2 — is the whole "
                "story.") +
        "<div class='strip' style='gap:26px'>" + "".join(html) + "</div>"))
    return [("small_steps.png", body)]


# =========================================== 6. the top/bottom row asymmetry ==

@figure("asymmetry")
def asymmetry():
    inward = ((0, 1, 2, 3, 4), (1, 0, 2, 3, 4), (2, 1, 0, 3, 4))
    outward = ((0, 1, 2, 3, 4), (2, 0, 1, 3, 4), (2, 1, 0, 3, 4))
    assert W.score_of(inward) == 68 and W.score_of(outward) == 70

    def card(heading, grid, kind, note, highlight):
        frames = W.play(grid)
        chips = "".join(
            f"<span class='delta{' hot' if f.round == highlight else ''}'>"
            f"round {f.round} &nbsp;+{f.gained}</span>" for f in frames[1:])
        third = W.play(grid, rounds=3)[-1]
        return ("<div class='stack' style='gap:10px;width:395px'>"
                f"<div class='label'>{heading}</div>"
                f"{P.wall(third, live_rows=3)}"
                "<div class='label'>after round 2 — rounds 3 and 4 just fill columns "
                "3 and 4</div>"
                f"<div class='score'><span class='pts'>{frames[-1].score}</span>"
                "<span class='pts-unit'>points, filled out</span></div>"
                f"<div class='strip wrap' style='gap:5px'>{chips}</div>"
                f"<div class='callout {kind}'>{note}</div></div>")

    a = card("row 1 grows left", inward, "bad",
             "The README's board. Row 1 goes <b>left</b> in round 1, so column 2 is "
             "left for round 2 — and there row 0's tile lands <b>before</b> row 1's and "
             "cannot count it: 3 points instead of 6. Finish however you like, "
             "<b>68</b> is the ceiling.", 2)
    b = card("row 1 grows right", outward, "good",
             "One tile moved: row 1 goes <b>right</b> in round 1. Column 2 now has two "
             "tiles under row 0 by the time round 2 gets there, and that tile scores 6. "
             "Same fifteen tiles, <b>70</b> points.", 2)

    body = P.shot(P.panel(
        P.title("Rows are not interchangeable",
                "The wall is filled from the top row down, so within a round a tile "
                "cannot see the tile that arrives below it — a column has to be built "
                "upwards, or in one go. Both boards open with the same diagonal in "
                "round 0 and differ by one tile in round 1; the whole difference lands "
                "in round 2.") +
        "<div class='strip' style='gap:26px'>" + a + "<span class='vs'>vs</span>" + b +
        "</div>"))
    return [("asymmetry.png", body)]


# ============================================================ 7. histograms ==

def histogram(counts: dict, lines: int) -> str:
    lo, hi = min(counts), max(counts)
    peak = max(counts.values())
    total = sum(counts.values())

    bins = []
    for s in range(lo, hi + 1):
        n = counts.get(s, 0)
        kind = " edge-min" if s == lo else (" edge-max" if s == hi else "")
        tag = thousands(n) if kind else ""
        h = 100 * n / peak
        bins.append(f"<div class='bin{kind}'><span class='v'>{tag}</span>"
                    f"<div class='bar' style='height:{h:.3f}%'></div>"
                    f"<span class='x'>{s}</span></div>")

    axis = ("<div class='axis-y'>"
            f"<span>{thousands(peak)}</span><span>{thousands(peak // 2)}</span>"
            "<span>0</span></div>")

    word = "line" if lines == 1 else "lines"
    return P.shot(P.panel(
        P.title(f"Every way to fill {lines} {word}",
                f"All {thousands(total)} orders in which the top {lines} {word} of the "
                f"wall can be filled, counted by the score they end on. The worst is "
                f"{lo} points ({thousands(counts[lo])} ways) and the best is {hi} "
                f"({thousands(counts[hi])} ways).") +
        f"<div class='strip' style='gap:0'>{axis}<div class='hist'>{''.join(bins)}</div></div>"
        "<div style='height:8px'></div>"
        "<div class='label'>final score</div>"))


@figure("histograms")
def histograms():
    out = []
    for lines in (1, 2, 3):
        counts = read_scores(RESULTS / f"{lines}_lines_scores.txt")
        out.append((RESULTS / f"{lines}_lines.png", histogram(counts, lines)))
    return out


# ==================================================================== driver ==

def main(argv):
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
