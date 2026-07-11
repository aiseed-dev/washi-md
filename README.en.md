# washi-md

[日本語](README.md) | English | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md)

Turn Markdown into **beautifully typeset Japanese documents** (HTML / PDF).
One command covers horizontal business documents, vertical-writing fiction,
and genkō yōshi (Japanese manuscript paper).

```bash
# Until the PyPI release, install from GitHub (dependency first):
pip install "mdit-py-cjk-friendly @ git+https://github.com/aiseed-dev/mdit-py-cjk-friendly.git"
pip install "washi-md @ git+https://github.com/aiseed-dev/washi-md.git"
# After the PyPI release: pip install washi-md

washi report.md          # → report.html (typeset, self-contained, one file)
washi report.md --pdf    # → report.pdf as well (headless Chrome/Chromium)
```

## What gets beautiful

- **Morisawa UD fonts first**: uses the commercial UD Reimin / UD Shin Go
  (Morisawa Fonts) when installed, falling back to BIZ UD → Hiragino / Noto.
  `--embed-fonts DIR` embeds BIZ UD woff2 (SIL OFL) into the HTML so the
  document looks the same on machines without the fonts
- **Japanese typesetting CSS included**: mincho body text, justification,
  first-line indent, line-height 1.9, gothic headings, line-start kinsoku
  (`line-break: strict`), punctuation trimming (`text-spacing-trim`),
  hanging punctuation
- **CJK-friendly Markdown parsing**
  ([mdit-py-cjk-friendly](https://github.com/aiseed-dev/mdit-py-cjk-friendly)):
  mid-sentence line breaks don't become spaces; emphasis works next to
  full-width brackets
- **Vertical writing and manuscript paper**: `--vertical` for right-to-left
  vertical text (with tate-chū-yoko), `--genko` for one-character-per-cell
  manuscript paper (both orientations)
- **Print/PDF ready**: `@page` with A4, margins, page numbers; avoids page
  breaks inside tables/code/after headings. `--pdf` uses headless Chrome
  (no extra dependencies)
- **Furigana (ruby)**: `{漢字|かんじ}` (group ruby) / `{東京|とう|きょう}`
  (mono ruby) — Denden Markdown notation; works in vertical writing too
- **Emphasis dots / lines**: `[text]{.sesame_dot}` (Pandoc-style class span) —
  bundled CSS for sesame / circle / triangle / double-circle / fisheye /
  saltire dots and solid-to-wavy lines, in both orientations
- Title block generated from frontmatter (`title` / `author` / `date`)

## Usage

```
washi INPUT.md [-o OUTPUT.html] [--title TITLE] [--pdf]
      [--theme default|textbook|gothic|maru|bungei]
      [--vertical] [--genko]
      [--font-serif NAME] [--font-sans NAME] [--webfonts]
      [--css FILE ...] [--no-base-css] [--embed-fonts DIR]
```

From Python:

```python
from washi_md import render
html = render(markdown_text, title="Report")
```

## Vertical writing

```bash
washi novel.md --vertical --theme bungei --pdf
```

`--vertical` typesets the body vertically (lines flow right to left).
One- and two-digit numbers are set upright via tate-chū-yoko; tables and
code blocks stay horizontal. Combine with the bungei theme for fiction.

Manuscript paper (genkō yōshi), in either orientation:

```bash
washi essay.md --genko --pdf              # horizontal manuscript paper
washi essay.md --genko --vertical --pdf   # vertical, 20 characters/line
```

One character per grid cell, full-width solid setting; half-width
alphanumerics are converted to full width automatically. Change the line
length with `--css` and `body.genko { --genko-cols: 25; }`.

## Themes and custom CSS

- `--theme textbook` — UD Digital Kyokasho-tai body (learning materials)
- `--theme gothic` — gothic body, no indent (business documents)
- `--theme maru` — rounded gothic (Zen Maru Gothic; soft notices)
- `--theme bungei` — old-style mincho (Shippori Mincho; literary)
- `--webfonts` — load Google Fonts so themes work without local fonts
- `--font-serif "A1 Mincho"` / `--font-sans "Shin Go M"` — use any
  installed font by name (Morisawa Fonts etc.); works for PDF too
- User themes: drop `~/.config/washi-md/themes/NAME.css` and use
  `--theme NAME`
- `--css my.css` — append your own CSS; `--no-base-css` — start from zero

## License

MIT
