"""Image output for the sim — PNG, labelled contact sheets, animated GIF.

Uses Pillow (authorised 2026-07-26, see `docs/dependencies.md`). This replaced a
hand-rolled PNG writer; the reason for the change was labels. Without text
rendering, a contact sheet has to have its reading order explained in prose
alongside the image, which makes the artifact incomplete on its own.

Everything here takes and returns numpy `uint8` arrays shaped (H, W, 3), which
is what `mujoco.Renderer.render()` produces.
"""

from __future__ import annotations

import pathlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Drawn over renders, so it has to read against both the pale deck and the dark
# skybox — hence the shadow rather than a plain fill.
_LABEL_FILL = (255, 255, 255)
_LABEL_SHADOW = (0, 0, 0)


def _font(size: int) -> ImageFont.ImageFont:
    """A real TrueType face if one is available, else Pillow's bitmap default.

    The default font does not scale, so on a fallback the labels come out small
    rather than absent — degraded, not broken.
    """
    for name in ("DejaVuSans.ttf", "arial.ttf", "Arial.ttf", "segoeui.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def save_png(path: pathlib.Path | str, pixels: np.ndarray) -> pathlib.Path:
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(pixels).save(path)
    return path


def label(pixels: np.ndarray, text: str, size: int = 22, pad: int = 12) -> np.ndarray:
    """Burn a caption into the top-left of a frame."""
    img = Image.fromarray(pixels.copy())
    draw = ImageDraw.Draw(img)
    font = _font(size)
    for dx, dy in ((1, 1), (2, 2)):
        draw.text((pad + dx, pad + dy), text, font=font, fill=_LABEL_SHADOW)
    draw.text((pad, pad), text, font=font, fill=_LABEL_FILL)
    return np.asarray(img)


def contact_sheet(
    frames: list[tuple[str, np.ndarray]],
    cols: int,
    path: pathlib.Path | str,
    number: bool = True,
) -> pathlib.Path:
    """Tile labelled frames into one image, reading left-to-right, top-to-bottom."""
    if not frames:
        raise ValueError("no frames to tile")

    h, w, _ = frames[0][1].shape
    rows = (len(frames) + cols - 1) // cols
    sheet = np.zeros((h * rows, w * cols, 3), dtype=np.uint8)

    for idx, (caption, frame) in enumerate(frames):
        text = f"{idx + 1}. {caption}" if number else caption
        r, c = divmod(idx, cols)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = label(frame, text)

    return save_png(path, sheet)


def save_gif(
    frames: list[np.ndarray],
    path: pathlib.Path | str,
    fps: int = 20,
    scale: float = 1.0,
) -> pathlib.Path:
    """Write an animated GIF.

    GIF is 256 colours, so Pillow quantises. MuJoCo's flat-shaded materials have
    a small palette to begin with, so this costs little here — but it is the
    reason a GIF of a photographic scene would look poor.
    """
    if not frames:
        raise ValueError("no frames to write")

    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    images = []
    for frame in frames:
        img = Image.fromarray(frame)
        if scale != 1.0:
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)), Image.LANCZOS
            )
        images.append(img.convert("P", palette=Image.ADAPTIVE, colors=256))

    images[0].save(
        path,
        save_all=True,
        append_images=images[1:],
        duration=max(20, int(1000 / fps)),
        loop=0,
        optimize=True,
        disposal=2,
    )
    return path
