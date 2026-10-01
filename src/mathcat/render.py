"""Render one matplotlib mathtext formula to PNG bytes.

This is not a TeX install. matplotlib.mathtext draws a single formula:
fractions, roots, integrals, Greek, subscripts, superscripts, \\mathrm, and
\\text. It rejects preamble commands, \\begin environments, and user macros.
"""

from __future__ import annotations

import io
import re
import threading

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

_LOCK = threading.Lock()
_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
_MAX_TEX = 8000


class FormulaError(ValueError):
    """The formula is empty or mathtext cannot parse it."""


def normalize_tex(tex: str) -> str:
    text = (tex or "").strip()
    if not text:
        raise FormulaError("empty formula")
    if len(text) > _MAX_TEX:
        raise FormulaError("formula too long")
    if text.startswith("$$") and text.endswith("$$"):
        text = "$" + text[2:-2].strip() + "$"
    elif not (text.startswith("$") and text.endswith("$")):
        text = f"${text}$"
    if text == "$$" or text == "$":
        raise FormulaError("empty formula")
    return text


def _check_color(value: str, label: str) -> str:
    if not _COLOR.match(value or ""):
        raise FormulaError(f"{label} must be #rgb or #rrggbb")
    return value


def render_png(
    tex: str,
    *,
    dpi: int = 220,
    color: str = "#f2f2f7",
    bg: str | None = None,
) -> bytes:
    """Return a PNG. ``bg`` None or ``\"transparent\"`` keeps the background transparent."""
    text = normalize_tex(tex)
    if not isinstance(dpi, int) or isinstance(dpi, bool) or not 72 <= dpi <= 600:
        raise FormulaError("dpi must be an integer from 72 to 600")
    color = _check_color(color, "color")
    transparent = bg is None or bg == "" or bg == "transparent"
    if not transparent:
        bg = _check_color(bg, "bg")

    with _LOCK:
        fig = plt.figure(figsize=(0.1, 0.1), dpi=dpi)
        try:
            if transparent:
                fig.patch.set_alpha(0)
            else:
                fig.patch.set_facecolor(bg)
            ax = fig.add_axes((0, 0, 1, 1))
            ax.axis("off")
            ax.set_facecolor("none" if transparent else bg)
            try:
                label = ax.text(0.0, 0.0, text, color=color, fontsize=22, ha="left", va="bottom")
                fig.canvas.draw()
            except Exception as exc:
                message = " ".join(str(exc).split()) or "could not parse formula"
                raise FormulaError(message) from exc
            bbox = label.get_window_extent(renderer=fig.canvas.get_renderer()).expanded(1.15, 1.45)
            bbox = bbox.transformed(fig.dpi_scale_trans.inverted())
            fig.set_size_inches(max(bbox.width, 0.6), max(bbox.height, 0.45))
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            label.set_position((0.5, 0.5))
            label.set_ha("center")
            label.set_va("center")
            buf = io.BytesIO()
            fig.savefig(
                buf,
                format="png",
                dpi=dpi,
                transparent=transparent,
                facecolor="none" if transparent else bg,
                bbox_inches="tight",
                pad_inches=0.15,
            )
            return buf.getvalue()
        finally:
            plt.close(fig)
