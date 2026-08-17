"""The HTML pieces the figures are built from: walls, score plates, captions."""

from __future__ import annotations

import html as _html

import wall as W

TILE = 32


def cell(row: int, col: int, frame, *, stamps=True, gap=False, spot=False,
         mark_fresh=False) -> str:
    color = W.color_at(row, col)
    classes = ["cell"]
    body = ""
    if (row, col) in frame.placed:
        classes.append("tile")
        if mark_fresh and (row, col) in frame.fresh:
            classes.append("fresh")
        if stamps:
            body = f"<span class='stamp'>{frame.stamps[(row, col)]}</span>"
    else:
        classes.append("empty")
        if gap:
            classes.append("gap")
    if spot:
        classes.append("spot")
    return f"<div class='{' '.join(classes)}' data-color='{color}'>{body}</div>"


def wall(frame, *, rows=W.SIZE, live_rows=None, stamps=True, gaps=(), spots=(),
         mark_fresh=False, tile=TILE, row_keys=False, row_notes=None) -> str:
    """A wall. Rows past ``live_rows`` are drawn greyed back.

    ``live_rows`` defaults to "as many rows as the figure is about", i.e. the
    rows the grid actually mentions — the other two are still drawn, because
    seeing that this is the top of a real 5×5 wall is half the explanation.
    """
    live = rows if live_rows is None else live_rows
    out = [f"<div class='wall' style='--tile:{tile}px'>"]
    for r in range(rows):
        muted = " muted" if r >= live else ""
        out.append(f"<div class='wall-row{muted}'>")
        for c in range(W.SIZE):
            out.append(cell(r, c, frame, stamps=stamps, gap=(r, c) in gaps,
                            spot=(r, c) in spots, mark_fresh=mark_fresh))
        out.append("</div>")
    out.append("</div>")
    body = "".join(out)
    if row_keys or row_notes:
        left = right = ""
        if row_keys:
            left = ("<div class='rowkeys'>" +
                    "".join(f"<span>{r}</span>" for r in range(rows)) + "</div>")
        if row_notes:
            right = ("<div class='rowkeys wide'>" +
                     "".join(f"<span>{n}</span>" for n in row_notes) + "</div>")
        body = (f"<div class='wallwrap' style='--tile:{tile}px'>"
                f"{left}{body}{right}</div>")
    return body


def grid_wall(grid, **kw) -> str:
    """A finished wall, straight from a README grid."""
    frames = W.play(grid)
    return wall(frames[-1], live_rows=kw.pop("live_rows", len(grid)), **kw)


def score(frame, *, delta=True, unit="points") -> str:
    d = ""
    if delta:
        if frame.gained:
            d = f"<span class='delta'>+{frame.gained} this round</span>"
        else:
            d = "<span class='delta none'>nothing placed yet</span>"
    return (f"<div class='score'><span class='pts'>{frame.score}</span>"
            f"<span class='pts-unit'>{unit}</span>{d}</div>")


def pips(current: int, total: int = W.SIZE) -> str:
    dots = "".join(f"<span class='pip{' on' if i <= current else ''}'></span>"
                   for i in range(total))
    return f"<div class='pips'>{dots}<span class='label' style='margin-left:8px'>" \
           f"{'round ' + str(current) if current >= 0 else 'empty board'}</span></div>"


def verdict(text: str, kind: str = "mid") -> str:
    return f"<span class='verdict {kind}'>{_html.escape(text)}</span>"


def title(text: str, sub: str = "") -> str:
    out = f"<h1 class='title'>{text}</h1>"
    if sub:
        out += f"<p class='subtitle'>{sub}</p>"
    return out


def panel(inner: str) -> str:
    return f"<div class='panel'>{inner}</div>"


def shot(inner: str) -> str:
    return f"<div class='shot'>{inner}</div>"


def board_card(grid, *, heading, note="", verdict_kind=None, verdict_text=None,
               tile=TILE, stamps=True, gaps=(), spots=(), live_rows=None) -> str:
    """One wall with its own little header: the unit these figures repeat."""
    frames = W.play(grid)
    head = f"<div class='label'>{heading}</div>"
    tag = verdict(verdict_text, verdict_kind) if verdict_text else ""
    body = wall(frames[-1], live_rows=live_rows if live_rows is not None else len(grid),
                stamps=stamps, gaps=gaps, spots=spots, tile=tile)
    foot = score(frames[-1], delta=False)
    extra = f"<p class='note'>{note}</p>" if note else ""
    return ("<div class='stack' style='gap:9px'>" + head + body + foot + tag + extra +
            "</div>")


def pattern_lines(tile=TILE) -> str:
    """The staircase on the left of a real board, empty."""
    out = [f"<div class='lines' style='--tile:{tile}px'>"]
    for r in range(W.SIZE):
        out.append("<div class='pline'>")
        out.append("<span class='slot'></span>" * (r + 1))
        out.append("</div>")
    out.append("</div>")
    return "".join(out)
