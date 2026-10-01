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

Show the formula with `mathcat`. Do not send it through an image generator. Do not install TeX. The README is only the install page.

## Show it

1. If stdout is the user's iTerm2, WezTerm, or Kitty, run `mathcat '<tex>'`. iTerm2 and WezTerm get the imgcat protocol. Kitty gets the Kitty protocol.
2. If stdout is a captured tool shell, do not run bare `mathcat`. It writes raw PNG bytes into the capture. Run `mathcat -o <path>.png '<tex>'`, then in the user's iTerm2 session run `imgcat <path>.png`.
3. On a terminal with no inline images (Ubuntu GNOME Terminal and most Linux consoles), `mathcat '<tex>'` prints a PNG path. Tell the user that path.
4. If `mathcat` is missing: `python3 -m pip install matplotlib` and `python3 -m pip install "git+https://github.com/johndpope/mathcat.git"`. From a checkout, `python3 -m pip install .` Then `mathcat` is on `PATH` (often `~/.local/bin`).

One formula per call. `$...$` wrappers are optional.

## Greek

When the formula contains Greek commands (`\pi`, `\alpha`, `\sigma`, and the rest of the mathtext Greek set), pass `--legend` unless the user asked for the formula alone.

```bash
mathcat --legend 'e^{i\pi}+1=0'
```

The formula stays white. Under it, each Greek letter that appears is listed once, in the order it appears, with its English name and a color that belongs to that letter. A variant uses a spoken name such as "curly phi" or "final sigma". A capital shares the color of its small letter. The map is `src/mathcat/legend.py`. Use `--legend` and leave the colors there.

Do not color symbols inside the formula. mathtext has no per-symbol color, and `\color` is rejected. Skip `--legend` when there is no Greek; the flag then changes nothing.

## Dialect

These work: fractions, roots, integrals, subscripts, superscripts, `\mathrm`, `\text`, and the Greek commands above.

```text
e^{i\pi}+1=0
x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}
\int_{-\infty}^{\infty} e^{-x^{2}}\,dx=\sqrt{\pi}
```

These do not: `\begin{...}` environments, `\usepackage`, `\newcommand`, TikZ, `\ce{}`, more than one formula in one call. A non-zero exit means the formula is outside this dialect. Simplify it to one line. Do not redraw it with an image model.

## More than one formula

Start `mathd` once. It listens on `http://127.0.0.1:8765`. Later `mathcat` calls use it. Leave the bind address on localhost.

`POST /png` with `{"tex":"..."}` returns `image/png`. In JSON a backslash is `\\`. Prefer POST. A raw `+` in a query string is a space. `GET /health` returns `{"ok":true,"service":"mathd"}`.

`mathcat --local` renders in-process and ignores `mathd`. `-o file.png` writes a file and does not display it.
