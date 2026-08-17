# viz: where the pictures come from

Every figure and GIF in the top-level README is generated from this directory.
Nothing is drawn by hand and no number on a figure is typed in. The boards come
from the grids in `../results/`, and the scores are computed by `wall.py`.

```
python3 viz/make_figures.py             # all of them, a few minutes
python3 viz/make_figures.py three_lines # just one
python3 viz/make_figures.py --list      # what there is
python3 viz/test_wall.py                # check the scoring against src/board.py
python3 viz/checks.py                   # check the published numbers
```

Figures are written to `../images/`; the three histograms overwrite
`../results/{1,2,3}_lines.png`.

Rows, columns and rounds are displayed 1 to 5. Internally everything is 0-based,
and so are the `results/*.txt` data files, so every display adds 1.

## Why a browser

The tiles are not images. `theme.css` is vendored, unmodified, from
[ludometer](https://github.com/RemiFabre/ludometer), the palette and the tile
bevel of a working Azul client by the same author, and `figure.css` draws with
it. So the boards in the README look like the game rather than like a plot, and
restyling everything is one file.

`render.py` renders a page in headless Chrome on a transparent background, trims
the transparency away, and hands back an image that is exactly the figure. No
code has to guess how wide a caption will be. GIF frames get a second pass on a
fixed canvas so the animation cannot jitter, then ffmpeg builds a single palette
for the whole sequence.

## Animation

`wall.steps()` returns one frame per tile, in the order the wall receives them
(top row first inside a round). `holds()` in `make_figures.py` turns that into
frame durations: a short beat between tiles, a longer one at the end of a round
so the round total can be read, and a long hold on the finished board. That is
why the GIFs make the top-row-first fill order visible, which is the fact most of
the analysis rests on.

## The files

| file | what it is |
|---|---|
| `wall.py` | the wall, its colours, and Azul's adjacency scoring. ~50 lines, no dependencies |
| `test_wall.py` | asserts `wall.py` agrees with `../src/board.py`, board for board |
| `checks.py` | recounts the distribution, the openings, and the one-round-per-hole rule |
| `parts.py` | HTML for a wall, a score plate, a round counter, a legend |
| `render.py` | HTML to PNG to GIF (Chrome, ImageMagick, ffmpeg, gifsicle, pngquant) |
| `make_figures.py` | one function per figure. This is the file to edit |
| `theme.css` | every colour, vendored from ludometer |
| `figure.css` | the tile, the wall, and the figure furniture |

## The figures

| name | output |
|---|---|
| `notation` | `images/notation.gif`, the numbering, static beside animated |
| `one_line` | `images/one_line.gif`, best and worst on one row |
| `two_lines` | `images/two_lines.gif`, obvious, best and worst on two rows |
| `three_lines` | `images/three_lines.gif`, the same on three rows. The hero figure |
| `double_count` | `images/double_count.gif`, the 2x2 example of the double count |
| `gaps` | `images/gaps.gif`, one column, three orders |
| `budget` | `images/column_budget.png`, the squares above a tile, marked |
| `forced` | `images/forced.png`, the position after round 2, one tile apart |
| `starters` | `images/starters_{best,worst}.png`, the openings |
| `bothsets` | `images/large_steps.png`, the two openings in both lists |
| `steps` | `images/small_steps.png`, the three staircase openings |
| `asymmetry` | `images/asymmetry.gif`, one tile, two points |
| `histograms` | `results/{1,2,3}_lines.png` |

## Requirements

`google-chrome` or `chromium`, ImageMagick (`convert`, `identify`), `ffmpeg`.
`gifsicle` and `pngquant` are optional. Without them the output is identical,
just several times larger. No Python packages are needed.
