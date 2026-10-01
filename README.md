<p align="center">
  English · <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <img src="docs/hero.jpg" alt="Pixel-art thriller: a laptop in the rain, a ribbon of light, and quantum formulas across the frame" width="100%">
</p>

<h1 align="center">mathcat</h1>

<p align="center">
  One math formula, drawn as a PNG.<br>
  macOS and Ubuntu. No TeX install.
</p>

## Install

Python 3.10 or newer.

```bash
python3 -m pip install matplotlib
python3 -m pip install git+https://github.com/johndpope/mathcat.git
mathcat 'e^{i\pi}+1=0'
```

`mathcat` lands on your `PATH`, usually at `~/.local/bin`. On iTerm2, pipe it if you want the picture inline:

```bash
mathcat 'e^{i\pi}+1=0' | imgcat
```

<p align="center">
  <img src="docs/euler.png" alt="Euler's identity" width="280">
</p>

```bash
mathcat --legend '\psi(x)=\int_{-\infty}^{\infty}\hat{\psi}(\xi)\,e^{2\pi i x \xi}\,d\xi'
```

<p align="center">
  <img src="docs/legend.png" alt="A formula with a colored ledger for psi, xi, and pi, then the integral limits, psi hat, and the exponent" width="640">
</p>

`--note` adds a short line in fine print under the ledger. Repeat it for another line. `$...$` inside a note draws as math.

```bash
mathcat --legend \
  --note '$\mu$ is the center of the bell.' \
  --note '$\sigma$ is how wide the bell is.' \
  'f(x)=\frac{1}{\sigma\sqrt{2\pi}}\exp\left(-\frac{(x-\mu)^{2}}{2\sigma^{2}}\right)'
```

<p align="center">
  <img src="docs/note.png" alt="A Gaussian with a colored ledger and two short notes under it" width="640">
</p>

## For an LLM

Do not invent a workflow from this page. Load the mathcat skill and follow it.

- Grok: [`.grok/skills/mathcat/SKILL.md`](.grok/skills/mathcat/SKILL.md)
- Claude: [`.claude/skills/mathcat/SKILL.md`](.claude/skills/mathcat/SKILL.md)

They are the same file. Install both so a chat in either tool can run it:

```bash
mkdir -p ~/.grok/skills ~/.claude/skills
ln -sfn /path/to/mathcat/.grok/skills/mathcat ~/.grok/skills/mathcat
ln -sfn /path/to/mathcat/.grok/skills/mathcat ~/.claude/skills/mathcat
```

`/mathcat` runs it. Asking to see a formula selects it.

People who want the flags, the ledger, the fine-print notes, and the pictures: [USAGE.md](USAGE.md).

## License

Copyright 2026 John D. Pope.

[Do No Harm License](LICENSE.md) (pre 1.0), the license at [raisely/NoHarm](https://github.com/raisely/NoHarm/blob/publish/LICENSE.md).
