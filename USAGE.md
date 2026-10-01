# Usage

Install is on the [README](README.md). If you are an LLM, follow the skill instead of this page: [`.grok/skills/mathcat/SKILL.md`](.grok/skills/mathcat/SKILL.md).

```bash
mathcat 'x=\frac{-b\pm\sqrt{b^{2}-4ac}}{2a}'
mathcat 'e^{i\pi}+1=0' | imgcat
mathcat -o formula.png 'E=mc^2'
```

On iTerm2 and WezTerm the picture is inline. Kitty draws it with the Kitty graphics protocol. Ubuntu GNOME Terminal, xterm, and the Linux console print a path to a PNG.

<p align="center">
  <img src="docs/quadratic.png" alt="Quadratic formula" width="420"><br>
  <img src="docs/gaussian.png" alt="Gaussian integral" width="420"><br>
  <img src="docs/bayes.png" alt="Bayes" width="420">
</p>

## Greek ledger

`--legend` keeps the formula white and lists each Greek letter underneath with its English name. The same letter keeps the same color every time. Letters inside the formula stay white.

```bash
mathcat --legend '\psi(x)=\int_{-\infty}^{\infty}\hat{\psi}(\xi)\,e^{2\pi i x \xi}\,d\xi'
```

<p align="center">
  <img src="docs/legend.png" alt="Formula with a colored ledger for psi, xi, and pi" width="640">
</p>

## A few flags

`mathcat --help` lists them.

| Flag | What it does |
| --- | --- |
| `--legend` | English names under a formula that uses Greek |
| `-o file.png` | Write a PNG and do not display it |
| `--local` | Render in this process |
| `--bg '#12141a'` | Opaque background. The default is transparent |

`mathd` is optional. It serves PNGs on `http://127.0.0.1:8765`. When it is running, `mathcat` uses it.

One formula per call. matplotlib mathtext: fractions, roots, integrals, subscripts, superscripts, `\mathrm`, `\text`, and Greek commands. No `\begin{...}` environments, no preamble, no TikZ.
