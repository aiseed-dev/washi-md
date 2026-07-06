"""washi-md: Markdown から美しい日本語文書 (HTML/PDF) を作る。

使い方:
    washi 入力.md                # → 入力.html (組版済み・自己完結)
    washi 入力.md --pdf          # → さらに 入力.pdf (Chrome ヘッドレス印刷)
    washi 入力.md -o 出力.html --title "表題"

frontmatter (--- で囲む) の title / author / date は表題部に使われる。
"""
from __future__ import annotations

import argparse
import html as _html
import re
import shutil
import subprocess
import sys
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_cjk_friendly import cjk_friendly

__version__ = "0.3.0"

_CSS = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")

# --embed-fonts で探す BIZ UD (SIL OFL。再配布可) の woff2 と @font-face 定義
_FONT_FILES = [
    ("BIZUDPMincho-Regular.woff2", "BIZ UDPMincho", 400),
    ("BIZUDPGothic-Regular.woff2", "BIZ UDPGothic", 400),
    ("BIZUDPGothic-Bold.woff2", "BIZ UDPGothic", 700),
    ("BIZUDGothic-Regular.woff2", "BIZ UDGothic", 400),
]


def _embed_fonts_css(fonts_dir: Path) -> str:
    """BIZ UD の woff2 を base64 の @font-face にする (見つかった分だけ)。"""
    import base64
    rules = []
    for fname, family, weight in _FONT_FILES:
        f = fonts_dir / fname
        if not f.exists():
            print(f"警告: {f} が無いため埋め込みをスキップ", file=sys.stderr)
            continue
        b64 = base64.b64encode(f.read_bytes()).decode()
        rules.append(
            f"@font-face {{ font-family: '{family}'; font-weight: {weight}; "
            f"font-display: swap; "
            f"src: url(data:font/woff2;base64,{b64}) format('woff2'); }}")
    return "\n".join(rules)

_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>
{heading}{body}
</body>
</html>
"""


def _frontmatter(text: str) -> tuple[dict, str]:
    m = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("'\"")
    return meta, text[m.end():]


THEMES_DIR = Path(__file__).parent / "themes"


def themes() -> list[str]:
    return sorted(["default"] + [f.stem for f in THEMES_DIR.glob("*.css")])


def render(text: str, title: str | None = None,
           embed_fonts: Path | None = None, theme: str = "default",
           extra_css: list[Path] | None = None, base_css: bool = True) -> str:
    """Markdown 文字列 → 自己完結の組版済み HTML。"""
    meta, body_md = _frontmatter(text)
    md = MarkdownIt("commonmark", {"html": True}).enable("table").use(cjk_friendly)
    body = md.render(body_md)

    title = title or meta.get("title")
    heading = ""
    if title and "<h1" not in body.split("\n", 3)[0]:
        heading = f"<h1>{_html.escape(title)}</h1>\n"
        sub = "　".join(filter(None, [meta.get("author"), meta.get("date")]))
        if sub:
            heading += f'<p class="doc-meta">{_html.escape(sub)}</p>\n'
    else:
        title = title or "文書"
    parts = [_CSS] if base_css else []
    if theme != "default":
        theme_file = THEMES_DIR / f"{theme}.css"
        if not theme_file.exists():
            raise ValueError(f"テーマがありません: {theme} (利用可能: {', '.join(themes())})")
        parts.append(theme_file.read_text(encoding="utf-8"))
    for f in extra_css or []:
        parts.append(Path(f).read_text(encoding="utf-8"))
    css = "\n".join(parts)
    if embed_fonts:
        css = _embed_fonts_css(Path(embed_fonts)) + "\n" + css
    return _PAGE.format(title=_html.escape(title), css=css,
                        heading=heading, body=body)


def _find_chrome() -> str | None:
    for c in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        if shutil.which(c):
            return c
    return None


def to_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = _find_chrome()
    if not chrome:
        sys.exit("PDF化には Chrome/Chromium が必要です (google-chrome または chromium)")
    subprocess.run(
        [chrome, "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri()],
        check=True, capture_output=True)


def main() -> None:
    ap = argparse.ArgumentParser(prog="washi", description=__doc__.split("\n")[0])
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path)
    ap.add_argument("--title")
    ap.add_argument("--pdf", action="store_true", help="Chrome ヘッドレスで PDF も出力")
    ap.add_argument("--theme", default="default",
                    help="文書テーマ (default / textbook / gothic)")
    ap.add_argument("--css", type=Path, action="append", default=[], metavar="FILE",
                    help="追加CSS (同梱CSSの後に適用。繰り返し指定可)")
    ap.add_argument("--no-base-css", action="store_true",
                    help="同梱CSSを使わず --css のみで組む")
    ap.add_argument("--embed-fonts", type=Path, metavar="DIR",
                    help="BIZ UD フォント (woff2) を HTML に埋め込む (SIL OFL)。"
                         "DIR に BIZUDPMincho-Regular.woff2 等を置く")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args()

    out = args.output or args.input.with_suffix(".html")
    out.write_text(render(args.input.read_text(encoding="utf-8"), args.title,
                          embed_fonts=args.embed_fonts, theme=args.theme,
                          extra_css=args.css, base_css=not args.no_base_css),
                   encoding="utf-8")
    print(out)
    if args.pdf:
        pdf = out.with_suffix(".pdf")
        to_pdf(out, pdf)
        print(pdf)


if __name__ == "__main__":
    main()
