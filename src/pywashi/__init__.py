"""pywashi: Markdown から美しい日本語文書 (HTML/PDF) を作る。

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
from html.parser import HTMLParser
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_cjk_friendly import bouten, cjk_friendly, ruby

__version__ = "0.10.1"

from .form import form  # [.form] ブロック → 対話的フォーム(opt-in プラグイン)

_CSS = (Path(__file__).parent / "style.css").read_text(encoding="utf-8")
_VERTICAL_CSS = (Path(__file__).parent / "vertical.css").read_text(encoding="utf-8")
_GENKO_CSS = (Path(__file__).parent / "genko.css").read_text(encoding="utf-8")

# フォームの描画資産(本文に [.form] がある時だけ、出力HTMLへ差し込む)
_FORM_DIR = Path(__file__).parent / "form_assets"
_FORM_CSS = (_FORM_DIR / "form.css").read_text(encoding="utf-8")
_FORM_JS = (_FORM_DIR / "form-render.js").read_text(encoding="utf-8")
_TURNSTILE = '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>'

# 縦中横: タグ・コード部を除いた本文テキスト中の 1〜2桁数字と !? ペア。
# <script>(フォーム定義JSON等)・<style> の中身はテキストではないので対象外
# —— ここを除外しないと [.form] のJSONに <span> が刺さって JSON.parse が
# 落ちる(縦書き+フォームのページでフォームが全滅した・実測)。文字参照
# (&#39; 等)も分解すると参照ごと壊れるため丸ごと素通しにする。
_TCY_SPLIT_RE = re.compile(
    r"(<pre\b.*?</pre>|<code\b.*?</code>|<script\b.*?</script>|"
    r"<style\b.*?</style>|<[^>]+>|&#?\w+;)", re.DOTALL)
_TCY_RE = re.compile(r"(?<![0-9A-Za-z])([0-9]{1,2}|[!?]{2})(?![0-9A-Za-z])")


def _tcy(html_body: str) -> str:
    """縦書き用: 短い英数字を <span class="tcy"> で縦中横にする。"""
    return "".join(
        p if p.startswith(("<", "&"))
        else _TCY_RE.sub(r'<span class="tcy">\1</span>', p)
        for p in _TCY_SPLIT_RE.split(html_body))


class _GenkoCellWrapper(HTMLParser):
    """原稿用紙(genko)用: 地の文の1文字を1マス <span class="cell"> で包む。

    背景のCSSグラデーションだけでマス目を描く旧方式は、フォントの行送り
    計算と理想値がわずかに食い違い、行を追うごとに文字とマス目がずれる
    （実測で確認）。文字そのものをマスの箱にして枠線を引けば、ずれは
    原理的に起きない。ルビの読み（rt/rp）・pre/code/table の中身は
    マス目の対象外（rt/rpは元々半角の添え物・pre/code/tableは横組みの
    まま埋め込む方針は変えない）。

    admonition(pyasciidocのNOTE:/WARNING:等が出す<div class="admonition
    ...">)も同様にマス目の対象外。1マス1文字方式は地の文の散文が前提で、
    ラベル+注記文というブロック構造とは噛み合わない（実際にgenko文書へ
    admonitionを混ぜてレンダリングし、ラベルの文字までマス目に分解されて
    崩れることを確認して対応）。
    """

    _SKIP_TAGS = {"rt", "rp", "pre", "code", "table", "script", "style"}
    # script/style は CDATA: マス目対象外なだけでなく、中身はHTMLテキスト
    # ではないのでエスケープもしない([.form] の定義JSONの `"` が &quot; に
    # 化けて JSON.parse が落ちた・実測)。HTMLParser は script/style 内で
    # 実体参照変換もタグ解釈もしないため、そのまま書き戻すのが正しい。
    _RAW_TAGS = {"script", "style"}
    # HTML整形用の半角空白（改行・タブ含む）だけをマス目対象外にする。
    # 全角スペース(U+3000、字下げに使われる)は str.isspace()==True だが
    # これは実際のマス1つぶんの中身なので、cellで包む対象に含める。
    _STRUCTURAL_WS = frozenset(" \t\n\r\f\v")

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self._skip_stack: list[str] = []
        # admonition div のネスト深さ(0=外)。stack名を使い回さないのは、
        # 万一admonition内にdivが入れ子になっても正しく数えられるように。
        self._admonition_depth = 0

    def _in_admonition(self) -> bool:
        return self._admonition_depth > 0

    def handle_starttag(self, tag: str, attrs) -> None:
        self.out.append(self.get_starttag_text() or f"<{tag}>")
        if tag in self._SKIP_TAGS:
            self._skip_stack.append(tag)
        if tag == "div":
            is_admonition = any(
                name == "class" and value and "admonition" in value
                for name, value in attrs
            )
            if is_admonition or self._in_admonition():
                self._admonition_depth += 1
        if tag == "p" and not self._in_admonition():
            # 段落先頭の字下げ(全角スペース1字ぶん)。地の文の字下げは
            # CommonMarkの行頭空白トリムで失われる（markdown-it自体が
            # 行頭の全角スペースも剥がす・実測で確認）ため、原稿用紙の
            # 慣例どおり段落先頭に空マスを1つ機械的に足す。
            # display:inlineのpにはtext-indentが効かない（仕様上非対応）
            # ため、この明示的な空マス方式に作り直した。admonition内の
            # p（ラベル・注記文）はマス目の対象外なので付けない。
            self.out.append('<span class="cell"></span>')

    def handle_startendtag(self, tag: str, attrs) -> None:
        self.out.append(self.get_starttag_text() or f"<{tag}/>")

    def handle_endtag(self, tag: str) -> None:
        self.out.append(f"</{tag}>")
        if self._skip_stack and self._skip_stack[-1] == tag:
            self._skip_stack.pop()
        if tag == "div" and self._admonition_depth > 0:
            self._admonition_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_stack and self._skip_stack[-1] in self._RAW_TAGS:
            self.out.append(data)  # script/style の中身は無加工で書き戻す
            return
        if self._skip_stack or self._in_admonition():
            self.out.append(_html.escape(data))
            return
        for ch in data:
            if ch in self._STRUCTURAL_WS:
                self.out.append(ch)  # HTML整形用の半角空白・改行は素通し
            else:
                self.out.append(f'<span class="cell">{_html.escape(ch)}</span>')


def _genko_cells(html_body: str) -> str:
    """本文HTML → 1文字1マスに包んだHTML（マス目はCSSの箱の枠線で描く）。"""
    p = _GenkoCellWrapper()
    p.feed(html_body)
    return "".join(p.out)

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
{scripts}</body>
</html>
"""


def _frontmatter(text: str) -> tuple[dict, str]:
    # \r?\n —— CRLF(Windows由来)の文書でも frontmatter を認識する
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip("'\"")
    return meta, text[m.end():]


THEMES_DIR = Path(__file__).parent / "themes"
USER_THEMES_DIR = Path.home() / ".config" / "pywashi" / "themes"


def _theme_file(name: str) -> Path | None:
    """ユーザーテーマ (~/.config/pywashi/themes/) が同梱テーマより優先。"""
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


def _build_parser(format: str) -> MarkdownIt:
    """入力方言(Markdown/AsciiDoc) → HTML化する MarkdownIt を組み立てる。

    フォント・組版CSS・縦書き/原稿用紙・PDF化はすべて入力方言と無関係
    (HTML文字列を受け取った後の処理)なので、ここでの分岐だけで
    render() 全体がAsciiDoc入力にも対応する。
    """
    if format == "markdown":
        return (MarkdownIt("commonmark", {"html": True})
                .enable("table").use(cjk_friendly).use(ruby).use(bouten).use(form))
    if format == "asciidoc":
        try:
            import pyasciidoc
        except ImportError as exc:
            raise ValueError(
                "format='asciidoc' には pyasciidoc が要ります "
                "(pip install pywashi[asciidoc] または pip install pyasciidoc)"
            ) from exc
        # pyasciidoc.asciidoc は内部で cjk_friendly を有効にする(見出し・
        # コメント・admonition・リスト・制約あり強調)。ふりがな(ruby)・
        # 傍点/傍線(bouten)はAsciiDoc構文には無いのでwashi側から追加で
        # 合成する(でんでん記法 {漢字|かんじ} 等はAsciiDoc本文中でも
        # そのまま使える)。
        # html:False —— AsciiDocに生HTML素通しの構文は無く、pyasciidoc
        # 自身も「render()はhtml:Falseで呼ぶ」前提で組んである。ここを
        # Trueにすると html_block(ブロック形の生HTML)だけが有効に残り、
        # <script>…</script> が素通しになる(pyasciidoc単体では防がれる
        # のに合成時だけXSS面が開く・実測)。
        return (MarkdownIt("commonmark", {"html": False})
                .enable("table").use(pyasciidoc.asciidoc).use(ruby).use(bouten).use(form))
    raise ValueError(f"未知のformat: {format!r}（'markdown'か'asciidoc'を指定）")


def render(text: str, title: str | None = None, author: str | None = None,
           embed_fonts: Path | None = None, theme: str = "default",
           extra_css: list[Path] | None = None, base_css: bool = True,
           webfonts: bool = False, font_serif: str | None = None,
           font_sans: str | None = None, vertical: bool = False,
           genko: bool = False, font_size: float | None = None,
           extra_style: str | None = None, format: str = "markdown") -> str:
    """Markdown(既定)またはAsciiDoc文字列 → 自己完結の組版済み HTML。

    author: 書誌の著者名（見出し直下に表示）。未指定ならfrontmatterの
        `author:` を使う（どちらも無ければ表示しない）。
    format: 'markdown'(既定)または'asciidoc'。AsciiDoc入力の解釈は
        別パッケージ pyasciidoc に委譲する(要 `pip install pyasciidoc`
        または `pip install pywashi[asciidoc]`)。ふりがな({漢字|かんじ})・
        傍点/傍線([対象]{.class})はどちらのformatでも共通して使える。
    font_size: 基準の文字サイズ(px)。既定CSSは15px（画面向け）なので、
        印刷では大きめを推奨 —— A4縦書きなら 24 で約40字/列、
        原稿用紙(genko)なら 24 で1マス約6.4mm（A4横置き）。
    extra_style: 生のCSSを末尾に足す（例 '@page{size:A4 landscape}'）。
    """
    meta, body_md = _frontmatter(text)
    md = _build_parser(format)
    body = md.render(body_md)
    has_form = 'class="fr-form"' in body  # [.form] が展開されたページだけ資産を積む
    if vertical and not genko:
        body = _tcy(body)  # 原稿用紙では縦中横にせず1字1マス (全角化) で組む

    title = title or meta.get("title")
    author = author or meta.get("author")
    heading = ""
    if title and "<h1" not in body.split("\n", 3)[0]:
        heading = f"<h1>{_html.escape(title)}</h1>\n"
        sub = "　".join(filter(None, [author, meta.get("date")]))
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
    if font_size:
        parts.append(f"html {{ font-size: {font_size}px; }}")
    for f in extra_css or []:
        parts.append(Path(f).read_text(encoding="utf-8"))
    if extra_style:
        parts.append(extra_style)
    if has_form:
        parts.append(_FORM_CSS)  # 自己完結: フォームCSSも同じ <style> に畳み込む
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
    if genko:
        # マス目は文字自身の箱の枠線で描く（背景グラデーションでは
        # 行送り計算の誤差で行を追うごとにずれるため・実測で確認済み）
        heading = _genko_cells(heading)
        body = _genko_cells(body)
    scripts = ""
    if has_form:
        # Turnstile(sitekey がある時だけ実際に描かれる)+ フォーム描画本体を
        # インライン化。form-render.js が .fr-form を自動初期化する。
        scripts = f"{_TURNSTILE}\n<script>\n{_FORM_JS}\n</script>\n"
    return _PAGE.format(title=_html.escape(title), css=css, bodyclass=bodyclass,
                        webfonts=webfont_links, heading=heading, body=body,
                        scripts=scripts)


def _find_chrome() -> str | None:
    for c in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        if shutil.which(c):
            return c
    return None


def to_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = _find_chrome()
    if not chrome:
        # ライブラリAPIなので sys.exit ではなく例外にする —— SystemExit は
        # Exception の派生ではないため、呼び出し側(bunko等)の
        # except Exception をすり抜けてワーカーごと黙って死んでいた。
        raise RuntimeError(
            "PDF化には Chrome/Chromium が必要です (google-chrome または chromium)")
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
    ap.add_argument("--format", choices=["markdown", "asciidoc"],
                    help="入力方言 (既定は拡張子で判定: .adoc/.asciidoc → "
                         "asciidoc、それ以外 → markdown。要 pyasciidoc)")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args()

    fmt = args.format or (
        "asciidoc" if args.input.suffix in (".adoc", ".asciidoc") else "markdown")

    out = args.output or args.input.with_suffix(".html")
    out.write_text(render(args.input.read_text(encoding="utf-8"), args.title,
                          embed_fonts=args.embed_fonts, theme=args.theme,
                          extra_css=args.css, base_css=not args.no_base_css,
                          webfonts=args.webfonts, font_serif=args.font_serif,
                          font_sans=args.font_sans, vertical=args.vertical,
                          genko=args.genko, format=fmt),
                   encoding="utf-8")
    print(out)
    if args.pdf:
        pdf = out.with_suffix(".pdf")
        try:
            to_pdf(out, pdf)
        except RuntimeError as exc:  # CLIでは従来どおりメッセージで終了
            sys.exit(str(exc))
        print(pdf)


if __name__ == "__main__":
    main()
