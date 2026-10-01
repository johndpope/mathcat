"""Show a PNG on the terminal, or say where it was written.

iTerm2 and WezTerm speak the same inline-image protocol as imgcat (OSC 1337).
Kitty speaks its own graphics protocol. Other terminals, including Ubuntu's
GNOME Terminal, get a file path.
"""

from __future__ import annotations

import base64
import os
import sys
import tempfile
from typing import BinaryIO


def detect_display() -> str:
    """Return ``iterm``, ``kitty``, or ``file``."""
    program = os.environ.get("TERM_PROGRAM", "")
    if os.environ.get("ITERM_SESSION_ID") or program in {"iTerm.app", "WezTerm"}:
        return "iterm"
    if os.environ.get("WEZTERM_PANE"):
        return "iterm"
    if os.environ.get("KITTY_WINDOW_ID") or os.environ.get("TERM") == "xterm-kitty":
        return "kitty"
    return "file"


def display_png(png: bytes, mode: str, out: BinaryIO) -> str | None:
    """Write the image to ``out``. Return a filesystem path only for file mode."""
    if mode == "auto":
        mode = detect_display() if out.isatty() else "stdout"
    if mode == "iterm":
        _write_iterm(png, out)
        return None
    if mode == "kitty":
        _write_kitty(png, out)
        return None
    if mode == "stdout":
        out.write(png)
        out.flush()
        return None
    path = _write_file(png)
    return path


def _write_file(png: bytes) -> str:
    handle = tempfile.NamedTemporaryFile(prefix="mathcat-", suffix=".png", delete=False)
    try:
        handle.write(png)
    finally:
        handle.close()
    return handle.name


def _write_iterm(png: bytes, out: BinaryIO) -> None:
    name = base64.standard_b64encode(b"formula.png")
    data = base64.standard_b64encode(png)
    body = b"1337;File=inline=1;size=%d;name=%s:%s" % (len(png), name, data)
    term = os.environ.get("TERM", "")
    if term.startswith(("screen", "tmux")):
        out.write(b"\033Ptmux;\033\033]" + body + b"\a\033\\")
    else:
        out.write(b"\033]" + body + b"\a")
    out.write(b"\n")
    out.flush()


def _write_kitty(png: bytes, out: BinaryIO) -> None:
    payload = base64.standard_b64encode(png)
    first = True
    while True:
        part = payload[:4096]
        payload = payload[4096:]
        more = 1 if payload else 0
        ctrl = f"a=T,f=100,m={more}" if first else f"m={more}"
        first = False
        out.write(f"\033_G{ctrl};".encode("ascii"))
        out.write(part)
        out.write(b"\033\\")
        if not payload:
            break
    out.write(b"\n")
    out.flush()


def stdout_is_tty() -> bool:
    return sys.stdout.isatty()
