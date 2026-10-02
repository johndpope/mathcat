<p align="center">
  <a href="README.md">English</a> · 日本語
</p>

<p align="center">
  <img src="docs/hero.jpg" alt="ピクセルアートのスリラー。雨のノートPC、光のリボン、量子の式が画面の内外に" width="100%">
</p>

<h1 align="center">mathcat</h1>

<p align="center">
  数式を一つ、PNG にする。<br>
  macOS と Ubuntu。TeX は不要。
</p>

## インストール

Python 3.10 以降。

```bash
python3 -m pip install matplotlib
python3 -m pip install git+https://github.com/johndpope/mathcat.git
mathcat 'e^{i\pi}+1=0'
```

`mathcat` は `PATH` に入ります。たいてい `~/.local/bin` です。iTerm2 で絵をその場に出すなら、パイプします。

```bash
mathcat 'e^{i\pi}+1=0' | imgcat
```

<p align="center">
  <img src="docs/euler.png" alt="オイラーの等式" width="280">
</p>

```bash
mathcat --legend '\psi(x)=\int_{-\infty}^{\infty}\hat{\psi}(\xi)\,e^{2\pi i x \xi}\,d\xi'
```

<p align="center">
  <img src="docs/legend.png" alt="ψ、ξ、π の色付き凡例と、積分の端、ψ ハット、指数" width="640">
</p>

`--note` は凡例の下に、小さい注を一行足します。もう一行足すときは、もう一度書きます。注の中の `$...$` は数式として描かれます。

```bash
mathcat --legend \
  --note '$\mu$ is the center of the bell.' \
  --note '$\sigma$ is how wide the bell is.' \
  'f(x)=\frac{1}{\sigma\sqrt{2\pi}}\exp\left(-\frac{(x-\mu)^{2}}{2\sigma^{2}}\right)'
```

<p align="center">
  <img src="docs/note.png" alt="ガウス分布。色付きの凡例と、その下に短い注が二つ" width="640">
</p>

## Claude Code

数式をペインに出す。端末が PNG を描き、モッドはパスだけを持つ。

```bash
claude --plugin-dir /path/to/mathcat
```

```
/mathcat
/mathcat e^{i\pi}+1=0
/mathcat --legend 'e^{i\pi}+1=0'
/mathcat drop
```

`/mathcat` でペインが開く。式を渡すと描いて残す。Prev、Next、Drop でその一覧を辿る。`--legend` と `--note` はコマンドと同じ。

Ghostty か kitty、Claude Code 2.1.287 以降。ほかの画面では式とパスを文字で出す。

## LLM 向け

このページから手順を作らないでください。mathcat のスキルを読み、それに従ってください。

- Grok: [`.grok/skills/mathcat/SKILL.md`](.grok/skills/mathcat/SKILL.md)
- Claude: [`.claude/skills/mathcat/SKILL.md`](.claude/skills/mathcat/SKILL.md)

中身は同じファイルです。どちらのツールでも使えるよう、両方に置きます。

```bash
mkdir -p ~/.grok/skills ~/.claude/skills
ln -sfn /path/to/mathcat/.grok/skills/mathcat ~/.grok/skills/mathcat
ln -sfn /path/to/mathcat/.grok/skills/mathcat ~/.claude/skills/mathcat
```

数式を見せてと頼むと、このスキルが選ばれます。ペインを入れた Claude Code では `/mathcat` がそのペインです。

フラグ、凡例、小さい注、図は [USAGE.md](USAGE.md)。USAGE は英語です。

## ライセンス

Copyright 2026 John D. Pope.

[Do No Harm License](LICENSE.md)（1.0 より前）。原文は [raisely/NoHarm](https://github.com/raisely/NoHarm/blob/publish/LICENSE.md) にあります。
