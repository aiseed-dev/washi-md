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
from mdit_py_cjk_friendly import bouten, cjk_friendly, ruby

__version__ = "0.9.0"

_CSS = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
_VERTICAL_CSS = (Path(__file__).parent / "vertical.css").read_text(encoding="utf-8")
_GENKO_CSS = (Path(__file__).parent / "genko.css").read_text(encoding="utf-8")

# 縦中横: タグ・コード部を除いた本文テキスト中の 1〜2桁数字と !? ペア
_TCY_SPLIT_RE = re.compile(r"(<pre\b.*?</pre>|<code\b.*?</code>|<[^>]+>)", re.DOTALL)
_TCY_RE = re.compile(r"(?<![0-9A-Za-z])([0-9]{1,2}|[!?]{2})(?![0-9A-Za-z])")


def _tcy(html_body: str) -> str:
    """縦書き用: 短い英数字を <span class="tcy"> で縦中横にする。"""
    return "".join(
        p if p.startswith("<") else _TCY_RE.sub(r'<span class="tcy">\1</span>', p)
        for p in _TCY_SPLIT_RE.split(html_body))

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

_WEBFONT_RE = re.compile(r"@webfonts:\s*([\w+@;:,]+)")
_GF_BASE = ("BIZ+UDPMincho", "BIZ+UDPGothic:wght@400;700", "BIZ+UDGothic")

_PAGE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
{webfonts}<style>
{css}
</style>
</head>
<body{bodyclass}>
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
USER_THEMES_DIR = Path.home() / ".config" / "washi-md" / "themes"


def _theme_file(name: str) -> Path | None:
    """ユーザーテーマ (~/.config/washi-md/themes/) が同梱テーマより優先。"""
    for d in (USER_THEMES_DIR, THEMES_DIR):
        f = d / f"{name}.css"
        if f.exists():
            return f
    return None


def themes() -> list[str]:
    names = {"default"}
    for d in (THEMES_DIR, USER_THEMES_DIR):
        if d.exists():
            names.update(f.stem for f in d.glob("*.css"))
    return sorted(names)


def render(text: str, title: str | None = None,
           embed_fonts: Path | None = None, theme: str = "default",
           extra_css: list[Path] | None = None, base_css: bool = True,
           webfonts: bool = False, font_serif: str | None = None,
           font_sans: str | None = None, vertical: bool = False,
           genko: bool = False) -> str:
    """Markdown 文字列 → 自己完結の組版済み HTML。"""
    meta, body_md = _frontmatter(text)
    md = (MarkdownIt("commonmark", {"html": True})
          .enable("table").use(cjk_friendly).use(ruby).use(bouten))
    body = md.render(body_md)
    if vertical and not genko:
        body = _tcy(body)  # 原稿用紙では縦中横にせず1字1マス (全角化) で組む

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
        theme_file = _theme_file(theme)
        if theme_file is None:
            raise ValueError(f"テーマがありません: {theme} (利用可能: {', '.join(themes())})")
        parts.append(theme_file.read_text(encoding="utf-8"))
    if vertical:
        parts.append(_VERTICAL_CSS)
    if genko:
        parts.append(_GENKO_CSS)
    if font_serif or font_sans:
        over = ":root {"
        if font_serif:
            over += f" --serif: '{font_serif}', 'BIZ UDPMincho', serif;"
        if font_sans:
            over += f" --sans: '{font_sans}', 'BIZ UDPGothic', sans-serif;"
        parts.append(over + " }")
    for f in extra_css or []:
        parts.append(Path(f).read_text(encoding="utf-8"))
    css = "\n".join(parts)
    if embed_fonts:
        css = _embed_fonts_css(Path(embed_fonts)) + "\n" + css

    webfont_links = ""
    if webfonts:
        fams = _WEBFONT_RE.findall(css) or []
        if base_css and theme == "default":
            fams = list(_GF_BASE) + fams
        elif base_css:
            fams = fams + list(_GF_BASE)  # テーマ書体を先に、UD代替も読む
        if fams:
            q = "&".join(f"family={f}" for f in dict.fromkeys(fams))
            webfont_links = (
                '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
                f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{q}&display=swap">\n')
    classes = [c for c, on in (("vertical", vertical), ("genko", genko)) if on]
    bodyclass = f' class="{" ".join(classes)}"' if classes else ""
    return _PAGE.format(title=_html.escape(title), css=css, bodyclass=bodyclass,
                        webfonts=webfont_links, heading=heading, body=body)


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
                    help="文書テーマ: " + " / ".join(themes()))
    ap.add_argument("--vertical", action="store_true",
                    help="縦書き (右→左の行送り。1〜2桁の数字は縦中横。"
                         "表とコードブロックは横書きのまま埋め込む)")
    ap.add_argument("--genko", action="store_true",
                    help="原稿用紙 (1字1マスのグリッド、20字/行)。"
                         "--vertical と併用で縦書き原稿用紙")
    ap.add_argument("--font-serif", metavar="NAME",
                    help="本文書体をインストール済みフォント名で指定 "
                         "(例: 'A1明朝'、'リュウミン R-KL'。Morisawa Fonts等)")
    ap.add_argument("--font-sans", metavar="NAME",
                    help="見出し書体をフォント名で指定 (例: '新ゴ M'、'フォーク M')")
    ap.add_argument("--webfonts", action="store_true",
                    help="Google Fonts を読み込む (フォント未導入の環境向け。"
                         "オフラインでは効かない)")
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
                          extra_css=args.css, base_css=not args.no_base_css,
                          webfonts=args.webfonts, font_serif=args.font_serif,
                          font_sans=args.font_sans, vertical=args.vertical,
                          genko=args.genko),
                   encoding="utf-8")
    print(out)
    if args.pdf:
        pdf = out.with_suffix(".pdf")
        to_pdf(out, pdf)
        print(pdf)


if __name__ == "__main__":
    main()
