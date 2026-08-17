"""Turn HTML into the PNGs and GIFs the README shows.

The drawing is done by a browser, because the tiles in ``figure.css`` are
gradients and shadows rather than bitmaps, and because that stylesheet is a
straight lift from a real Azul client — so the figures look like the game
instead of like a plot.

The trick that keeps this simple: the page background is transparent, we
screenshot a window that is deliberately too big, and then trim the
transparency away. The image is therefore exactly the figure, and no code has
to predict how wide a caption will be.

Requires ``google-chrome`` (or ``chromium``), ImageMagick's ``convert``, and —
for GIFs — ``ffmpeg`` and optionally ``gifsicle``.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCALE = 2  # render at 2x, so the PNGs stay crisp on a retina screen


def _browser() -> str:
    for name in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        if shutil.which(name):
            return name
    raise SystemExit("need google-chrome or chromium on PATH to render figures")


def _tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"need {name} on PATH to render figures")
    return path


def page(body: str, size: tuple[int, int] | None = None) -> str:
    """Wrap a figure body in a document that carries the whole palette."""
    theme = (HERE / "theme.css").read_text()
    figure = (HERE / "figure.css").read_text()
    fixed = ""
    if size:
        # Animation frames must all come out the same size, so the ground is
        # pinned rather than left to the content.
        fixed = f".shot {{ width: {size[0]}px; height: {size[1]}px; }}"
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{theme}</style><style>{figure}</style><style>{fixed}</style>"
        f"</head><body>{body}</body></html>"
    )


def shoot(body: str, out: Path, size: tuple[int, int] | None = None,
          window: tuple[int, int] = (2400, 2000), scale: int = SCALE,
          squeeze: bool = True) -> tuple[int, int]:
    """Render one figure to ``out``. Returns its size in CSS pixels."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "figure.html"
        html.write_text(page(body, size))
        raw = Path(tmp) / "raw.png"
        subprocess.run(
            [
                _browser(), "--headless=new", "--disable-gpu", "--no-sandbox",
                "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
                "--default-background-color=00000000",
                f"--force-device-scale-factor={scale}",
                f"--window-size={window[0]},{window[1]}",
                "--virtual-time-budget=1500",
                f"--user-data-dir={tmp}/profile",
                f"--screenshot={raw}", str(html),
            ],
            check=True, capture_output=True,
        )
        subprocess.run([_tool("convert"), str(raw), "-trim", "+repage", "-strip", str(out)],
                       check=True)
    w, h = _size(out)
    if squeeze:
        _squeeze(out)
    return w // scale, h // scale


def _squeeze(png: Path) -> None:
    """Palette-quantise a figure. Roughly 4x smaller, no visible difference —
    these are flat panels with a handful of gradients, not photographs."""
    if not shutil.which("pngquant"):
        return
    subprocess.run(["pngquant", "--quality=88-98", "--speed", "1", "--force",
                    "--output", str(png), str(png)], check=False)


def _size(png: Path) -> tuple[int, int]:
    out = subprocess.run([_tool("identify"), "-format", "%w %h", str(png)],
                         check=True, capture_output=True, text=True).stdout
    w, h = out.split()
    return int(w), int(h)


def shoot_series(bodies: list[str], into: Path, stem: str = "frame") -> list[Path]:
    """Render frames that are guaranteed to share one canvas size.

    Pass one: draw them free and measure. Pass two: redraw them all on the
    largest ground any of them needed. Without this, a score going from 9 to 10
    points widens the figure and the GIF jitters.
    """
    into.mkdir(parents=True, exist_ok=True)
    sizes = [shoot(b, into / f"{stem}-probe-{i:03d}.png", squeeze=False)
             for i, b in enumerate(bodies)]
    for probe in into.glob(f"{stem}-probe-*.png"):
        probe.unlink()

    canvas = (max(w for w, _ in sizes), max(h for _, h in sizes))
    paths = []
    for i, body in enumerate(bodies):
        path = into / f"{stem}-{i:03d}.png"
        # no per-frame quantising: ffmpeg builds one palette for the whole
        # animation, and pre-quantised frames make it flicker
        shoot(body, path, size=canvas, squeeze=False)
        paths.append(path)
    return paths


def gif(frames: list[Path], out: Path, holds: list[int], fps: int = 4,
        downscale: bool = True) -> None:
    """Assemble a GIF.

    ``holds[i]`` is how many ticks of ``1/fps`` frame *i* stays on screen — the
    last board wants a long pause, the intermediate rounds a short one. Repeats
    are written out as real frames because a constant frame rate is what lets
    ffmpeg build one good palette for the whole animation; GIF has 256 colours
    to spend and these tiles are all gradient.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        seq = Path(tmp)
        n = 0
        for frame, hold in zip(frames, holds):
            for _ in range(max(1, hold)):
                target = seq / f"f{n:04d}.png"
                if downscale:
                    # rendered at 2x; halving it is a free antialiasing pass
                    subprocess.run([_tool("convert"), str(frame), "-resize", "50%",
                                    str(target)], check=True)
                else:
                    shutil.copy(frame, target)
                n += 1
        subprocess.run(
            [
                _tool("ffmpeg"), "-y", "-loglevel", "error",
                "-framerate", str(fps), "-i", str(seq / "f%04d.png"),
                "-vf", "split[a][b];[a]palettegen=max_colors=224:stats_mode=full[p];"
                       "[b][p]paletteuse=dither=sierra2_4a",
                "-loop", "0", str(out),
            ],
            check=True,
        )
    if shutil.which("gifsicle"):
        subprocess.run(["gifsicle", "-O3", "--batch", str(out)],
                       check=True, capture_output=True)
