"""Render one formula. Inline in iTerm2, WezTerm, and Kitty. PNG elsewhere."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

from mathcat.display import display_png
from mathcat.legend import compose_legend
from mathcat.render import FormulaError, render_png

_DEFAULT_URL = "http://127.0.0.1:8765"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mathcat",
        description="Render a mathtext formula. On iTerm2 and WezTerm this uses the imgcat protocol.",
    )
    parser.add_argument("tex", nargs="+", help="formula, for example e^{i\\pi}+1=0")
    parser.add_argument("-o", "--output", help="write a PNG to this path instead of displaying it")
    parser.add_argument(
        "--url",
        default=os.environ.get("MATHCAT_URL", _DEFAULT_URL),
        help="mathd base URL. Use --local to skip it.",
    )
    parser.add_argument("--local", action="store_true", help="render in this process even if mathd is running")
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--color", default="#f2f2f7")
    parser.add_argument("--bg", default=None, help='opaque background such as #1c1c1e, or "transparent"')
    parser.add_argument("--display", choices=["auto", "iterm", "kitty", "file"], default="auto")
    parser.add_argument(
        "--legend",
        action="store_true",
        help="add a ledger naming Greek letters, accents, subscripts, and superscripts",
    )
    parser.add_argument(
        "--note",
        action="append",
        default=[],
        help="a short intuitive note in fine print under the formula; repeat for more lines",
    )
    args = parser.parse_args(argv)
    tex = " ".join(args.tex).strip()

    try:
        png = _render(tex, args)
        if args.legend or args.note:
            png = compose_legend(tex, png, dpi=args.dpi, legend=args.legend, notes=args.note)
    except FormulaError as exc:
        print(f"mathcat: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "wb") as handle:
            handle.write(png)
        print(os.path.abspath(args.output))
        return 0

    out = sys.stdout.buffer
    mode = args.display
    if mode == "auto" and not out.isatty():
        mode = "stdout"
    path = display_png(png, mode, out)
    if path:
        print(path)
    return 0


def _render(tex: str, args) -> bytes:
    if not args.local and args.url and _healthy(args.url):
        return _fetch(args.url, tex, args.dpi, args.color, args.bg)
    return render_png(tex, dpi=args.dpi, color=args.color, bg=args.bg)


def _healthy(url: str) -> bool:
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/health", timeout=0.3) as response:
            return response.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _fetch(url: str, tex: str, dpi: int, color: str, bg: str | None) -> bytes:
    body = json.dumps({"tex": tex, "dpi": dpi, "color": color, "bg": bg}).encode("utf-8")
    request = urllib.request.Request(
        url.rstrip("/") + "/png",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")
        try:
            detail = json.loads(detail).get("error", detail)
        except json.JSONDecodeError:
            pass
        raise FormulaError(detail) from exc
    if not data.startswith(b"\x89PNG"):
        raise FormulaError("mathd did not return a PNG")
    return data


if __name__ == "__main__":
    raise SystemExit(main())
