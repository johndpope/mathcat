---
name: mathcat
description: >
  Render a TeX-style math formula to PNG and show it inline with the iTerm2
  imgcat protocol (also WezTerm), Kitty, or a PNG file on Ubuntu and other
  terminals. Use when the user asks to show, typeset, or display a formula,
  equation, LaTeX, or math in the terminal, or runs /mathcat. When Greek
  letters appear, use --legend for the English-name color ledger. Use the
  mathcat tools, not an image generator and not a full TeX install.
---

# mathcat

Show formulas with `mathcat` / `mathd`. The install, HTTP API, and mathtext dialect are in the README at https://github.com/johndpope/mathcat — follow that file for flags and for what TeX is accepted. Do not restate it.

## Show a formula

1. If stdout is the user's iTerm2, WezTerm, or Kitty, run `mathcat '<tex>'`. That writes the imgcat protocol on iTerm2 and WezTerm.
2. If stdout is a captured tool shell, do not run bare `mathcat`. It would dump PNG bytes into the capture. Run `mathcat -o <path>.png '<tex>'`, then in the user's iTerm2 session run `imgcat <path>.png`.
3. On a terminal with no inline images (Ubuntu GNOME Terminal and most Linux consoles), `mathcat '<tex>'` prints a PNG path. Tell the user that path.
4. If `mathcat` is not installed: `python3 -m pip install matplotlib` and `python3 -m pip install -e .` from a checkout, or `pip install git+https://github.com/johndpope/mathcat.git`. `python3 -m mathcat '<tex>'` works with `PYTHONPATH=src`.

## Greek ledger

When the formula contains Greek commands (`\pi`, `\alpha`, `\sigma`, and the rest of the mathtext Greek set), pass `--legend` unless the user asked for the formula alone.

`mathcat --legend '<tex>'` keeps the formula in white and draws a ledger under it: the glyph, then its English name. A variant uses a spoken name such as "curly phi" or "final sigma". A capital shares the color of its small letter.

The colors live in `src/mathcat/legend.py`. Use `--legend` and leave them there. Do not wrap symbols in `\color` — mathtext rejects it — and do not recolor the formula. Skip `--legend` when the formula has no Greek; the flag then changes nothing.

## Repeated renders

Start `mathd` once. It listens on `http://127.0.0.1:8765`. Later `mathcat` calls use it. `POST /png` with `{"tex":"..."}` returns `image/png`. A non-zero `mathcat` exit means the formula is outside mathtext: simplify it. Do not redraw it with an image model.
