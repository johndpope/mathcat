<p align="center">
  <img src="docs/hero.jpg" alt="A ribbon of light rising off a laptop on a dark desk" width="100%">
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

<details>
<summary>Pictures, Greek ledger, and the rest of the flags</summary>

<p align="center">
  <img src="docs/quadratic.png" alt="Quadratic formula" width="420"><br>
  <img src="docs/gaussian.png" alt="Gaussian integral" width="420"><br>
  <img src="docs/bayes.png" alt="Bayes" width="420">
</p>

`--legend` keeps the formula white and lists each Greek letter underneath with its English name. The same letter keeps the same color every time. Letters inside the formula stay white.

```bash
mathcat --legend '\psi(x)=\int_{-\infty}^{\infty}\hat{\psi}(\xi)\,e^{2\pi i x \xi}\,d\xi'
```

<p align="center">
  <img src="docs/legend.png" alt="Formula with a colored ledger for psi, xi, and pi" width="640">
</p>

`mathcat --help` lists the flags. `mathd` is an optional localhost service on port 8765. The skill is the full set of rules for rendering, display, and the mathtext dialect.

</details>

## License

Copyright 2026 John Pope.

[Do No Harm License](LICENSE.md) (pre 1.0), the license at [raisely/NoHarm](https://github.com/raisely/NoHarm/blob/publish/LICENSE.md).
