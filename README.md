<p align="center">
  <img src="docs/hero.jpg" alt="A ribbon of light rising off a laptop on a dark desk" width="100%">
</p>

<h1 align="center">mathcat</h1>

<p align="center">
  One math formula, drawn as a PNG, on the machine you are already on.<br>
  macOS and Ubuntu. No TeX install.
</p>

<p align="center">
  <img src="docs/mark.jpg" alt="A glowing curve" width="180">
</p>

```bash
mathcat 'e^{i\pi}+1=0'
mathcat 'e^{i\pi}+1=0' | imgcat
```

On iTerm2 and WezTerm that is the same inline-image protocol as [imgcat](https://iterm2.com/utilities/imgcat). Kitty gets the Kitty graphics protocol. Ubuntu’s GNOME Terminal, and anything else without inline images, gets a PNG file.

A small `mathd` process can sit on `127.0.0.1:8765` and hand those PNGs to anything that can speak HTTP. `mathcat` uses it when it is up, and renders on its own when it is not.

## Four formulas

<table>
  <tr>
    <td align="center"><img src="docs/quadratic.png" alt="Quadratic formula" width="360"><br>quadratic</td>
    <td align="center"><img src="docs/euler.png" alt="Euler identity" width="280"><br>Euler</td>
  </tr>
  <tr>
    <td align="center"><img src="docs/gaussian.png" alt="Gaussian integral" width="360"><br>Gaussian integral</td>
    <td align="center"><img src="docs/bayes.png" alt="Bayes theorem" width="360"><br>Bayes</td>
  </tr>
</table>

The pictures above are real output from `mathcat`, not illustrations.

## A ledger for Greek letters

The formula stays white. When you pass `--legend`, each Greek letter that appears is listed under it with an English name and a color that belongs to that letter.

```bash
mathcat --legend '\psi(x)=\int_{-\infty}^{\infty}\hat{\psi}(\xi)\,e^{2\pi i x \xi}\,d\xi'
```

<p align="center">
  <img src="docs/legend.png" alt="A formula with a colored ledger: psi, xi, pi" width="640">
</p>

`\pi` is pi, and it is the same green every time. `\Pi` uses that same green. Variants get a spoken name: curly phi, final sigma, curly epsilon. The map lives in [`src/mathcat/legend.py`](src/mathcat/legend.py). mathtext cannot color a single symbol inside a formula, so the color stays in the ledger.

Skip `--legend` when you want the formula by itself, or when there is no Greek in it. The flag then changes nothing.

## For LLMs

Use mathcat instead of an image generator. Image models invent symbols.

```bash
mathcat -o formula.png 'e^{i\pi}+1=0'
imgcat formula.png
```

- If your shell is the user’s iTerm2, WezTerm, or Kitty, run `mathcat '<tex>'` with no `-o`.
- If your shell is a captured tool runner, `-o` a PNG and `imgcat` that file in the user’s iTerm2 session. A bare `mathcat` there writes raw PNG bytes into the capture.
- On a terminal with no inline images, `mathcat` prints a path. Tell the user that path.
- More than one formula: start `mathd`, then keep calling `mathcat`.
- HTTP is `POST /png` with `{"tex":"..."}` and an `image/png` body. A raw `+` in a query string is a space, so prefer POST.
- One formula per call. matplotlib mathtext, not full LaTeX. See [Dialect](#dialect).
- Greek letters: add `--legend` unless the user asked for the formula alone. Do not invent colors and do not wrap symbols in `\color`.
- A non-zero exit means the formula is outside mathtext. Simplify it. Do not switch to an image model.
- Leave `mathd` on `127.0.0.1`.

The Grok skill that follows these rules is [`.grok/skills/mathcat/SKILL.md`](.grok/skills/mathcat/SKILL.md).

`GET /health` returns `{"ok": true, "service": "mathd"}`.

## Install

Python 3.10 or newer, and matplotlib. The same commands on macOS and Ubuntu:

```bash
python3 -m pip install matplotlib
python3 -m pip install git+https://github.com/johndpope/mathcat.git
```

From a checkout, `python3 -m pip install .` is the same thing. `mathcat` and `mathd` need to be on `PATH` (`~/.local/bin` is the usual place).

```bash
mathcat --local -o /tmp/euler.png 'e^{i\pi}+1=0'
```

That file should be a PNG.

### Where the picture shows up

| Terminal | What you see |
| --- | --- |
| iTerm2, WezTerm | The formula, inline |
| Kitty | The formula, inline |
| GNOME Terminal, xterm, the Linux console | A path to a PNG |

WezTerm on Ubuntu already understands the imgcat protocol. GNOME Terminal does not. Open the file, or pass `-o`.

To keep the service running on Ubuntu, [`contrib/mathd.service`](contrib/mathd.service) expects `~/.local/bin/mathd`:

```bash
mkdir -p ~/.config/systemd/user
cp contrib/mathd.service ~/.config/systemd/user/mathd.service
systemctl --user enable --now mathd.service
```

On macOS, run `mathd` in a terminal, or point a LaunchAgent at `mathd --host 127.0.0.1 --port 8765`.

## Use

```bash
mathd   # optional; leave this running
```

```bash
mathcat 'x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}'
mathcat --legend 'e^{i\pi}+1=0'
mathcat --local 'E=mc^2'          # ignore mathd for this call
mathcat -o quadratic.png 'x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}'
```

`MATHCAT_URL` or `--url` points at a different service address.

### HTTP

```bash
curl -fsS http://127.0.0.1:8765/health

curl -fsS -X POST http://127.0.0.1:8765/png \
  -H 'content-type: application/json' \
  -d '{"tex":"e^{i\\pi}+1=0"}' \
  -o euler.png
```

The shell line is single-quoted, so the server receives `\pi`. In JSON a backslash is written `\\`.

```bash
curl -fsS --get http://127.0.0.1:8765/png \
  --data-urlencode 'tex=e^{i\pi}+1=0' \
  -o euler.png
```

Optional fields, on GET and POST: `dpi` from 72 to 600 (default 220), `color` as `#rgb` or `#rrggbb` (default `#f2f2f7`), `bg` in the same form, or `transparent`. Leave `bg` out for a transparent PNG, which sits cleanly on a dark terminal. The gallery images in this README use `#12141a` so they stay readable on a light page.

A bad formula is HTTP 400 and `{"error":"..."}`.

## Dialect

The renderer is [matplotlib mathtext](https://matplotlib.org/stable/users/explain/text/mathtext.html). `$...$` and `$$...$$` are optional.

These work:

```text
e^{i\pi}+1=0
x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}
\int_{-\infty}^{\infty} e^{-x^{2}}\,dx=\sqrt{\pi}
P(A\mid B)=\frac{P(B\mid A)\,P(A)}{P(B)}
\mathrm{speed}
\text{speed}
```

These do not:

- `\begin{align}`, `\begin{matrix}`, and other environments
- `\usepackage`, `\newcommand`, `\documentclass`
- TikZ, chemistry `\ce{}`, diagrams
- More than one formula in one call

## Skill

Copy the skill into your Grok home and it is available in every project:

```bash
mkdir -p ~/.grok/skills
ln -sfn /path/to/mathcat/.grok/skills/mathcat ~/.grok/skills/mathcat
```

`/mathcat` runs it. Asking to see a formula selects it from the description.

## Development

```bash
python3 -m pip install matplotlib
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

GitHub Actions runs that on Ubuntu for Python 3.10 and 3.12.

## License

MIT.
