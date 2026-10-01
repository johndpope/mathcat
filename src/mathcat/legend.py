"""Optional ledger. The formula stays white. Color lives only in the ledger.

Each Greek command has one English name and one color. The same command is the
same color in every ledger. Accents, subscripts, and superscripts that the
formula uses are read aloud after the Greek ("x hat", "x sub i", "x squared").
matplotlib mathtext cannot color individual symbols, so the formula PNG is left
untouched and the ledger is drawn underneath it.
"""

from __future__ import annotations

import io
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.mathtext import MathTextParser
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

# Accent command, spoken suffix.
_ACCENTS = {
    "hat": "hat",
    "widehat": "hat",
    "bar": "bar",
    "overline": "bar",
    "tilde": "tilde",
    "widetilde": "tilde",
    "vec": "vector",
    "dot": "dot",
    "ddot": "double dot",
}
# Commands whose limits read "from ... to ...".
_LIMIT_OPERATORS = {"int", "oint", "iint", "iiint", "sum", "prod", "coprod", "bigcup", "bigcap"}
# Commands whose subscript reads "as ..." or "over ...".
_UNDER_OPERATORS = {"lim": "as", "max": "over", "min": "over", "sup": "over", "inf": "over"}
# Superscripts with their own spoken name.
_POWERS = {"2": "squared", "3": "cubed", "T": "transpose", r"\prime": "prime", r"\dagger": "dagger", r"\ast": "star", "*": "star", "-1": "inverse"}
_NOTATION_COLOR = "#c9d1d9"
_MATHTEXT = MathTextParser("path")


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


def notation_in(tex: str) -> list[tuple[str, str, str, str]]:
    """Accents, subscripts, and superscripts in ``tex``, in order, once each.

    Each item is ``(key, glyph, spoken, color)``. ``glyph`` and ``spoken`` may hold
    mathtext between ``$`` signs, for example ``("x_i", "$x_i$", "$x$ sub $i$", ...)``.
    """
    tex = tex or ""
    found: list[tuple[str, str, str, str]] = []
    seen: set[str] = set()

    def add(glyph: str, spoken: str) -> None:
        if glyph in seen or not _parses(glyph) or not _parses(spoken):
            return
        seen.add(glyph)
        found.append((glyph, f"${glyph}$", spoken, _NOTATION_COLOR))

    base: str | None = None
    base_command: str | None = None
    command_start: int | None = None
    groups: list[int] = []
    parens: list[int] = []
    i = 0
    while i < len(tex):
        c = tex[i]
        if c.isspace():
            i += 1
            continue
        if c in "_^":
            arg, end = _argument(tex, i + 1)
            if base and arg:
                glyph = f"{base}{c}{{{arg}}}"
                add(glyph, _script_name(base, base_command, c, arg))
            i = end
            command_start = None
            continue
        if c == "\\":
            name, end = _command(tex, i)
            if name in _ACCENTS:
                arg, end = _argument(tex, end)
                if arg:
                    glyph = f"\\{name}{{{arg}}}"
                    add(glyph, f"${arg}$ {_ACCENTS[name]}")
                    base, base_command = glyph, None
                i = end
                command_start = None
                continue
            base, base_command = tex[i:end], name
            command_start = i
            i = end
            continue
        if c == "{":
            groups.append(command_start if command_start is not None else i)
            base = base_command = command_start = None
            i += 1
            continue
        if c == "}":
            if groups:
                base, base_command = tex[groups.pop() : i + 1], None
            i += 1
            command_start = None
            continue
        if c == "(":
            # f(x)^2 reads as "f(x) squared", not "(x) squared".
            follows = base is not None and i > 0 and tex[i - 1] == base[-1] and tex.endswith(base, 0, i)
            parens.append(i - len(base) if follows else i)
            base = None
        elif c == ")":
            base = tex[parens.pop() : i + 1] if parens else None
        elif c.isdigit():
            end = i
            while end < len(tex) and tex[end].isdigit():
                end += 1
            base = tex[i:end]
            i = end
            base_command = command_start = None
            continue
        elif c.isalpha():
            base = c
        else:
            base = None
        base_command = command_start = None
        i += 1
    return found


def legend_entries(tex: str) -> list[tuple[str, str, str, str]]:
    """Greek letters first, then accents and scripts."""
    return greek_in(tex) + notation_in(tex)


def _command(tex: str, i: int) -> tuple[str, int]:
    end = i + 1
    while end < len(tex) and tex[end].isalpha():
        end += 1
    if end == i + 1 and end < len(tex):
        end += 1
    return tex[i + 1 : end], end


def _argument(tex: str, i: int) -> tuple[str, int]:
    """One script or accent argument: a braced group, a command, or one character."""
    while i < len(tex) and tex[i].isspace():
        i += 1
    if i >= len(tex):
        return "", i
    if tex[i] == "{":
        depth = 0
        for end in range(i, len(tex)):
            if tex[end] == "{":
                depth += 1
            elif tex[end] == "}":
                depth -= 1
                if depth == 0:
                    return tex[i + 1 : end].strip(), end + 1
        return "", len(tex)
    if tex[i] == "\\":
        _name, end = _command(tex, i)
        return tex[i:end], end
    return tex[i], i + 1


def _script_name(base: str, command: str | None, mark: str, arg: str) -> str:
    if mark == "_":
        if command in _LIMIT_OPERATORS:
            return f"${base}$ from ${arg}$"
        if command in _UNDER_OPERATORS:
            return f"${base}$ {_UNDER_OPERATORS[command]} ${arg}$"
        return f"${base}$ sub ${arg}$"
    if command in _LIMIT_OPERATORS:
        return f"${base}$ to ${arg}$"
    if arg in _POWERS:
        return f"${base}$ {_POWERS[arg]}"
    return f"${base}$ to the ${arg}$"


def _parses(text: str) -> bool:
    try:
        _MATHTEXT.parse(text, dpi=72)
    except Exception:
        return False
    return True


def compose_legend(tex: str, formula_png: bytes, *, dpi: int = 220) -> bytes:
    """Return ``formula_png`` unchanged, or a dark card with the formula and a ledger."""
    entries = legend_entries(tex)
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
    """Formula, plus a ledger when Greek, accents, or scripts are present."""
    png = render_png(tex, **kwargs)
    return compose_legend(tex, png, dpi=kwargs.get("dpi", 220))


def _ledger_png(entries: list[tuple[str, str, str, str]], dpi: int) -> bytes:
    rows = len(entries)
    wide = any(glyph.startswith("$") for _key, glyph, _name, _color in entries)
    name_x = 0.34 if wide else 0.24
    fig = plt.figure(figsize=(4.4 if wide else 3.4, 0.42 * rows + 0.08), dpi=dpi)
    fig.patch.set_alpha(0)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    for index, (_command, glyph, name, color) in enumerate(entries):
        y = 1 - (index + 0.5) / rows
        ax.text(
            0.04,
            y,
            glyph,
            color=color,
            fontsize=16,
            ha="left",
            va="center",
            fontfamily="DejaVu Sans",
        )
        ax.text(
            name_x,
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
