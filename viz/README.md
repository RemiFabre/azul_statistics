# viz — where the pictures come from

Every figure and GIF in the top-level README is generated from this directory.
Nothing is drawn by hand and no number on a figure is typed in: the boards come
from the grids in `../results/`, and the scores are computed by `wall.py`.

```
python3 viz/make_figures.py             # all of them, ~40 s
python3 viz/make_figures.py filling     # just one (see the list below)
python3 viz/test_wall.py                # check the scoring against src/board.py
```

Figures are written to `../images/`; the three histograms overwrite
`../results/{1,2,3}_lines.png`.

## Why a browser

The tiles are not images. `theme.css` is vendored, unmodified, from
[ludometer](https://github.com/RemiFabre/ludometer) — the palette and the tile
bevel of a working Azul client, by the same author — and `figure.css` draws with
it. So the boards in the README look like the game rather than like a plot, and
restyling everything is one file.

`render.py` renders a page in headless Chrome on a transparent background,
trims the transparency away, and hands back an image that is exactly the figure.
No code has to guess how wide a caption will be. GIF frames get a second pass on
a fixed canvas so the animation cannot jitter, then ffmpeg builds a single
palette for the whole sequence.

## The files

| file | what it is |
|---|---|
| `wall.py` | the wall, its colours, and Azul's adjacency scoring — ~50 lines, no dependencies |
| `test_wall.py` | asserts `wall.py` agrees with `../src/board.py`, board for board |
| `parts.py` | HTML for a wall, a score plate, a round counter, a legend |
| `render.py` | HTML → PNG → GIF (Chrome, ImageMagick, ffmpeg, gifsicle, pngquant) |
| `make_figures.py` | one function per figure; this is the file to edit |
| `theme.css` | every colour, vendored from ludometer |
| `figure.css` | the tile, the wall, and the figure furniture |

## The figures

| name | file |
|---|---|
| `reading` | `images/reading.png` — the notation, and what a player board is |
| `filling` | `images/filling.gif` + `.png` — 68 / 70 / 47, round by round |
| `scoring` | `images/scoring.png` — why a tile can be worth seven |
| `gaps` | `images/gaps.png` — the same column, three orders |
| `starters` | `images/starters_{best,worst}.png` — the openings |
| `bothsets` | `images/large_steps.png` — the two openings in both lists |
| `steps` | `images/small_steps.png` — 2·2·2 vs 2·2·1 vs 1·2·2 |
| `asymmetry` | `images/asymmetry.png` — one tile, two points |
| `histograms` | `results/{1,2,3}_lines.png` |

## Requirements

`google-chrome` or `chromium`, ImageMagick (`convert`, `identify`), `ffmpeg`.
`gifsicle` and `pngquant` are optional — without them the output is identical,
just several times larger. No Python packages are needed.
