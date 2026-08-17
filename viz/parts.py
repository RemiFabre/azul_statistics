"""The HTML pieces the figures are built from: walls, score plates, captions.

Rows, columns and rounds are numbered 1 to 5 everywhere a reader can see them.
Internally they are 0-based, so every display of one adds 1.
"""

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
            body = f"<span class='stamp'>{frame.stamps[(row, col)] + 1}</span>"
    else:
        classes.append("empty")
        if gap:
            classes.append("gap")
    if spot:
        classes.append("spot")
    return f"<div class='{' '.join(classes)}' data-color='{color}'>{body}</div>"


def wall(frame, *, rows=W.SIZE, live_rows=None, stamps=True, gaps=(), spots=(),
         mark_fresh=False, tile=TILE, row_keys=False, row_notes=None) -> str:
    """A wall. Rows past ``live_rows`` are drawn greyed back."""
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
                    "".join(f"<span>{r + 1}</span>" for r in range(rows)) + "</div>")
        if row_notes:
            right = ("<div class='rowkeys wide'>" +
                     "".join(f"<span>{n}</span>" for n in row_notes) + "</div>")
        body = (f"<div class='wallwrap' style='--tile:{tile}px'>"
                f"{left}{body}{right}</div>")
    return body


def score(frame, *, delta=True, unit="points", running=True) -> str:
    """The score plate. ``delta`` adds what this round has earned so far."""
    d = ""
    if delta:
        if frame.gained:
            d = f"<span class='delta'>+{frame.gained} this round</span>"
        else:
            d = "<span class='delta none'>round 1</span>"
    return (f"<div class='score'><span class='pts'>{frame.score}</span>"
            f"<span class='pts-unit'>{unit}</span>{d}</div>")


def pips(current: int, total: int = W.SIZE, suffix="") -> str:
    """A row of dots for which round we are in. ``current`` is 0-based."""
    dots = "".join(f"<span class='pip{' on' if i <= current else ''}'></span>"
                   for i in range(total))
    label = f"round {current + 1} of {total}" if current >= 0 else "before round 1"
    return (f"<div class='pips'>{dots}<span class='label' style='margin-left:8px'>"
            f"{label}{suffix}</span></div>")


def verdict(text: str, kind: str = "mid") -> str:
    return f"<span class='verdict {kind}'>{_html.escape(text)}</span>"


def title(text: str, sub: str = "") -> str:
    out = f"<h1 class='title'>{text}</h1>"
    if sub:
        out += f"<p class='subtitle'>{sub}</p>"
    return out


def panel(inner: str, width: str = "") -> str:
    style = f" style='max-width:{width}'" if width else ""
    return f"<div class='panel'{style}>{inner}</div>"


def shot(inner: str) -> str:
    return f"<div class='shot'>{inner}</div>"


def label(text: str) -> str:
    return f"<div class='label'>{text}</div>"


def note(text: str, width="") -> str:
    style = f" style='max-width:{width}'" if width else ""
    return f"<p class='note'{style}>{text}</p>"


def chips(frames, highlight=None) -> str:
    """One pill per round: what that round earned."""
    out = []
    for f in frames:
        hot = " hot" if f.round == highlight else ""
        out.append(f"<span class='delta{hot}'>round {f.round + 1} &nbsp;"
                   f"+{f.gained}</span>")
    return f"<div class='strip wrap' style='gap:5px'>{''.join(out)}</div>"


def pattern_lines(tile=TILE) -> str:
    """The staircase on the left of a real board, empty."""
    out = [f"<div class='lines' style='--tile:{tile}px'>"]
    for r in range(W.SIZE):
        out.append("<div class='pline'>")
        out.append("<span class='slot'></span>" * (r + 1))
        out.append("</div>")
    out.append("</div>")
    return "".join(out)
