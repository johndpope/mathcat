"""Optional Greek ledger. The formula stays white. Color lives only in the ledger.

Each command has one English name and one color. The same command is the same
color in every ledger. matplotlib mathtext cannot color individual symbols, so
the formula PNG is left untouched and the ledger is drawn underneath it.
"""

from __future__ import annotations

import io
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

from mathcat.render import render_png

# Command, glyph, spoken name, color. Colors are the single palette.
_LETTERS: tuple[tuple[str, str, str, str], ...] = (
    ("alpha", "α", "alpha", "#ff7b72"),
    ("beta", "β", "beta", "#79c0ff"),
    ("gamma", "γ", "gamma", "#d2a8ff"),
    ("delta", "δ", "delta", "#ffa657"),
    ("epsilon", "ε", "epsilon", "#7ee787"),
    ("varepsilon", "ϵ", "curly epsilon", "#56d364"),
    ("zeta", "ζ", "zeta", "#ff9bce"),
    ("eta", "η", "eta", "#a5d6ff"),
    ("theta", "θ", "theta", "#f2cc60"),
    ("vartheta", "ϑ", "curly theta", "#e3b341"),
    ("iota", "ι", "iota", "#d2d8e0"),
    ("kappa", "κ", "kappa", "#ffa198"),
    ("lambda", "λ", "lambda", "#bc8cff"),
    ("mu", "μ", "mu", "#f778ba"),
    ("nu", "ν", "nu", "#56d4dd"),
    ("xi", "ξ", "xi", "#c3e88d"),
    ("pi", "π", "pi", "#3fb950"),
    ("varpi", "ϖ", "curly pi", "#56d364"),
    ("rho", "ρ", "rho", "#ffb86c"),
    ("varrho", "ϱ", "curly rho", "#e3b341"),
    ("sigma", "σ", "sigma", "#ff7eb6"),
    ("varsigma", "ς", "final sigma", "#ffb3d9"),
    ("tau", "τ", "tau", "#89ddff"),
    ("upsilon", "υ", "upsilon", "#ffcb6b"),
    ("phi", "φ", "phi", "#c792ea"),
    ("varphi", "ϕ", "curly phi", "#d2a8ff"),
    ("chi", "χ", "chi", "#f07178"),
    ("psi", "ψ", "psi", "#82aaff"),
    ("omega", "ω", "omega", "#ff9e64"),
    ("Gamma", "Γ", "Gamma", "#d2a8ff"),
    ("Delta", "Δ", "Delta", "#ffa657"),
    ("Theta", "Θ", "Theta", "#f2cc60"),
    ("Lambda", "Λ", "Lambda", "#bc8cff"),
    ("Xi", "Ξ", "Xi", "#c3e88d"),
    ("Pi", "Π", "Pi", "#3fb950"),
    ("Sigma", "Σ", "Sigma", "#ff7eb6"),
    ("Upsilon", "Υ", "Upsilon", "#ffcb6b"),
    ("Phi", "Φ", "Phi", "#c792ea"),
    ("Psi", "Ψ", "Psi", "#82aaff"),
    ("Omega", "Ω", "Omega", "#ff9e64"),
)

_BY_COMMAND = {command: (glyph, name, color) for command, glyph, name, color in _LETTERS}
_COMMAND = re.compile(r"\\([A-Za-z]+)")
_CARD = (18, 20, 26, 255)


def greek_in(tex: str) -> list[tuple[str, str, str, str]]:
    """Greek commands in ``tex``, in order, once each.

    Each item is ``(command, glyph, english_name, color)``.
    """
    found: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()
    for match in _COMMAND.finditer(tex or ""):
        command = match.group(1)
        if command in seen or command not in _BY_COMMAND:
            continue
        seen.add(command)
        glyph, name, color = _BY_COMMAND[command]
        found.append((command, glyph, name, color))
    return found


def compose_legend(tex: str, formula_png: bytes, *, dpi: int = 220) -> bytes:
    """Return ``formula_png`` unchanged, or a dark card with the formula and a ledger."""
    entries = greek_in(tex)
    if not entries:
        return formula_png
    formula = Image.open(io.BytesIO(formula_png)).convert("RGBA")
    ledger = Image.open(io.BytesIO(_ledger_png(entries, dpi))).convert("RGBA")
    pad = max(28, dpi // 6)
    gap = max(18, dpi // 10)
    width = max(formula.width, ledger.width) + pad * 2
    height = pad + formula.height + gap + ledger.height + pad
    card = Image.new("RGBA", (width, height), _CARD)
    card.paste(formula, ((width - formula.width) // 2, pad), formula)
    card.paste(ledger, ((width - ledger.width) // 2, pad + formula.height + gap), ledger)
    buf = io.BytesIO()
    card.save(buf, format="PNG")
    return buf.getvalue()


def render_legend_png(tex: str, **kwargs) -> bytes:
    """Formula, plus a ledger when Greek commands are present."""
    png = render_png(tex, **kwargs)
    return compose_legend(tex, png, dpi=kwargs.get("dpi", 220))


def _ledger_png(entries: list[tuple[str, str, str, str]], dpi: int) -> bytes:
    rows = len(entries)
    fig = plt.figure(figsize=(3.4, 0.38 * rows + 0.08), dpi=dpi)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    for index, (_command, glyph, name, color) in enumerate(entries):
        y = 1 - (index + 0.5) / rows
        ax.text(
            0.06,
            y,
            glyph,
            color=color,
            fontsize=16,
            ha="left",
            va="center",
            fontfamily="DejaVu Sans",
        )
        ax.text(
            0.24,
            y,
            name,
            color="#f2f2f7",
            fontsize=12,
            ha="left",
            va="center",
            fontfamily="DejaVu Sans",
        )
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return buf.getvalue()
