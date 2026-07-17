"""pywashi の検査。

render(Markdown→自己完結HTML)を厚く、CLI(main)は一巡だけ。
PDF(Chrome ヘッドレス)は環境依存のため Chrome がある場合のみ実行。
"""
import re
import sys
from pathlib import Path

import pytest

import pywashi
from pywashi import _find_chrome, _tcy, render, themes


# ---- render: 基本 ----


def test_self_contained_html():
    out = render("# 見出し\n\n本文です。\n")
    assert out.startswith("<!DOCTYPE html>")
    assert '<html lang="ja">' in out
    assert "<style>" in out  # CSS が埋め込まれた自己完結 HTML
    assert "<h1>見出し</h1>" in out
    assert "<p>本文です。</p>" in out


def test_table_enabled():
    out = render("| 項目 | 値 |\n|---|---|\n| a | 1 |\n")
    assert "<table>" in out
    assert "<th>項目</th>" in out


def test_cjk_softbreak_no_space():
    """和文のソフト改行に空白を入れない(mdit-py-cjk-friendly の適用確認)。"""
    out = render("これは長い\n文章です。\n")
    assert "これは長い文章です。" in out


def test_cjk_emphasis_next_to_punctuation():
    """全角約物に隣接する強調が成立する。"""
    out = render("a**あ、**b\n")
    assert "<strong>あ、</strong>" in out


# ---- frontmatter・表題 ----


def test_frontmatter_title_author_date():
    out = render("---\ntitle: 報告書\nauthor: 山田\ndate: 2026-07-09\n---\n\n本文。\n")
    assert "<title>報告書</title>" in out
    assert "<h1>報告書</h1>" in out
    assert '<p class="doc-meta">山田　2026-07-09</p>' in out


def test_title_argument_wins():
    out = render("---\ntitle: A\n---\n\n本文。\n", title="B")
    assert "<title>B</title>" in out
    assert "<h1>B</h1>" in out


def test_no_heading_when_body_starts_with_h1():
    out = render("# 既にある見出し\n", title="別の表題")
    assert out.count("<h1") == 1  # 二重の h1 を作らない


def test_title_escaped():
    out = render("本文。\n", title="<s>x</s>")
    assert "&lt;s&gt;x&lt;/s&gt;" in out
    assert "<s>x</s>" not in out


def test_default_title():
    out = render("本文。\n")
    assert "<title>文書</title>" in out


# ---- 縦書き・原稿用紙 ----


def test_vertical_class_and_tcy():
    out = render("令和8年7月9日!!\n", vertical=True)
    assert 'class="vertical"' in out
    assert '<span class="tcy">8</span>' in out
    assert '<span class="tcy">!!</span>' in out


def test_tcy_skips_three_digits_and_code():
    body = _tcy("<p>100年と2年</p><code>x = 12</code>")
    assert '<span class="tcy">2</span>' in body
    assert "100年" in body and "tcy\">100" not in body  # 3桁はそのまま
    assert "<code>x = 12</code>" in body  # コード内は触らない


def test_genko_class_without_tcy():
    out = render("昭和2年。\n", vertical=True, genko=True)
    assert 'class="vertical genko"' in out
    assert "tcy" not in out.split("</style>")[-1]  # 原稿用紙では縦中横にしない


def test_genko_wraps_every_character_in_a_cell():
    """マス目は文字自身の箱(<span class="cell">)——文字数+段落先頭の
    字下げマス1つぶん出る。"""
    out = render("メロスは激怒した。\n", vertical=True, genko=True)
    body = out.split("<body", 1)[1]
    assert body.count('class="cell"') == len("メロスは激怒した。") + 1
    assert '<p><span class="cell"></span><span class="cell">メ</span>' in body


def test_genko_ideographic_space_gets_its_own_cell():
    """全角スペース(U+3000)はマスを1つ占める（段落先頭の字下げはCommonMark
    の仕様で行頭空白として別途トリムされるため、文中の全角空白で検証）。"""
    out = render("間に　空白がある文。\n", vertical=True, genko=True)
    body = out.split("<body", 1)[1]
    assert body.count('class="cell"') == len("間に　空白がある文。") + 1
    assert '<span class="cell">　</span>' in body


def test_genko_ruby_base_gets_cells_but_reading_does_not():
    """ルビの親文字は1文字1マス、読み(rt/rp)はマス化の対象外。"""
    out = render("{吾輩|わがはい}は猫である。\n", vertical=True, genko=True)
    body = out.split("<body", 1)[1]
    assert '<span class="cell">吾</span><span class="cell">輩</span>' in body
    assert '<rt>わがはい</rt>' in body
    assert '<span class="cell">わ</span>' not in body


def test_genko_first_cell_is_first_child_of_its_paragraph():
    """CSSの.cell:first-childで開始側の枠線を閉じるため、各段落の最初の
    要素が直接<span class="cell">であること（間に他の要素を挟まない）。"""
    out = render("一行目。\n\n二行目。\n", vertical=True, genko=True)
    body = out.split("<body", 1)[1]
    assert body.count("<p>") == 2
    assert body.count('<p><span class="cell">') == 2


def test_genko_paragraph_gets_leading_indent_cell():
    """段落先頭に空マス1つ(字下げ)を機械的に足す —— display:inlineの<p>には
    text-indentが効かない(CSS仕様上非対応)ため、明示的な空セルで代替。
    地の文自身の全角スペースはCommonMarkの行頭空白トリムで失われる
    （markdown-it自体が剥がす）ため、この機械挿入が字下げの実体になる。"""
    out = render("字下げなしで書いた文。\n", vertical=True, genko=True)
    body = out.split("<body", 1)[1]
    assert '<p><span class="cell"></span><span class="cell">字</span>' in body


def test_genko_admonition_is_not_cell_wrapped():
    """admonition(pyasciidocのNOTE:等が出す<div class="admonition">)は
    1マス1文字方式の対象外 —— ラベル+注記文というブロック構造は原稿用紙の
    マス目と噛み合わない(実際にgenko文書へ混ぜてレンダリングし、ラベルの
    文字までマス目に分解されて崩れることを確認して対応)。"""
    text = (
        "本文。\n\n"
        '<div class="admonition note">\n'
        '<p class="admonition-label">NOTE</p>\n'
        "<p>注記の中身。</p>\n"
        "</div>\n\n"
        "続きの本文。\n"
    )
    out = render(text, vertical=True, genko=True)
    body = out.split("<body", 1)[1]
    assert '<p class="admonition-label">NOTE</p>' in body
    assert "<p>注記の中身。</p>" in body
    assert '<span class="cell">N</span>' not in body
    assert '<span class="cell">注</span>' not in body
    # admonition前後の地の文は変わらずマス化される
    assert '<span class="cell">本</span>' in body
    assert '<span class="cell">続</span>' in body


def test_genko_admonition_paragraphs_stay_block_display():
    """admonition内の<p>はgenko既定のdisplay:inline化(平文向けリセット)を
    打ち消すCSSが同梱されている。受けないままだとラベルと本文が1行に
    混ざって読めなくなる。"""
    out = render("dummy\n", vertical=True, genko=True)
    css = out.split("<style>", 1)[1].split("</style>", 1)[0]
    assert ".admonition p" in css and "display: block" in css


def test_render_author_param_shows_in_doc_meta():
    out = render("本文。\n", title="表題", author="作者名")
    assert '<p class="doc-meta">作者名</p>' in out


def test_render_author_falls_back_to_frontmatter():
    out = render("---\ntitle: 表題\nauthor: front名義\n---\n本文。\n")
    assert '<p class="doc-meta">front名義</p>' in out


# ---- テーマ・CSS ----


def test_themes_list():
    names = themes()
    assert "default" in names
    for bundled in ("bungei", "gothic", "maru", "textbook"):
        assert bundled in names


def test_unknown_theme_raises():
    with pytest.raises(ValueError, match="テーマがありません"):
        render("本文。\n", theme="そんなテーマない")


def test_bundled_theme_applied():
    base = render("本文。\n")
    themed = render("本文。\n", theme="gothic")
    assert len(themed) > len(base)  # テーマ CSS が追加されている


def test_no_base_css_and_extra_css(tmp_path):
    extra = tmp_path / "x.css"
    extra.write_text("body { color: red; }", encoding="utf-8")
    out = render("本文。\n", base_css=False, extra_css=[extra])
    assert "color: red" in out
    assert "--serif" not in out  # 同梱 CSS は入っていない


def test_font_override():
    out = render("本文。\n", font_serif="A1明朝", font_sans="新ゴ M")
    assert "--serif: 'A1明朝'" in out
    assert "--sans: '新ゴ M'" in out


def test_webfonts_link():
    on = render("本文。\n", webfonts=True)
    off = render("本文。\n")
    assert "fonts.googleapis.com" in on
    assert "fonts.googleapis.com" not in off


# ---- CLI ----


def test_cli_writes_html(tmp_path, monkeypatch, capsys):
    src = tmp_path / "doc.md"
    src.write_text("---\ntitle: T\n---\n\n本文。\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["washi", str(src)])
    pywashi.main()
    out_path = tmp_path / "doc.html"
    assert out_path.exists()
    assert "<h1>T</h1>" in out_path.read_text(encoding="utf-8")
    assert str(out_path) in capsys.readouterr().out


def test_cli_output_and_title(tmp_path, monkeypatch):
    src = tmp_path / "in.md"
    src.write_text("本文。\n", encoding="utf-8")
    dst = tmp_path / "out.html"
    monkeypatch.setattr(sys, "argv", ["washi", str(src), "-o", str(dst), "--title", "表題"])
    pywashi.main()
    assert "<title>表題</title>" in dst.read_text(encoding="utf-8")


# ---- PDF(Chrome がある環境のみ)----


@pytest.mark.skipif(_find_chrome() is None, reason="Chrome/Chromium なし")
def test_pdf(tmp_path, monkeypatch):
    src = tmp_path / "doc.md"
    src.write_text("# PDF テスト\n\n本文。\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["washi", str(src), "--pdf"])
    pywashi.main()
    pdf = tmp_path / "doc.pdf"
    assert pdf.exists()
    assert pdf.read_bytes()[:5] == b"%PDF-"


def test_ruby_group():
    html = render("{漢字|かんじ}を書く。")
    assert "<ruby>漢字<rp>(</rp><rt>かんじ</rt><rp>)</rp></ruby>" in html


def test_ruby_mono_with_vertical():
    html = render("{東京|とう|きょう}", vertical=True)
    assert "<ruby>東<rp>(</rp><rt>とう</rt><rp>)</rp>" in html
    assert "writing-mode: vertical-rl" in html


# ---- format="asciidoc"(要 pyasciidoc) ----


def test_asciidoc_format_renders_headings_emphasis_admonition_list():
    pytest.importorskip("pyasciidoc")
    html = render(
        "= 表題\n\nこれは*重要*です。\n\nNOTE: 補足の注記。\n\n* 項目1\n* 項目2\n",
        format="asciidoc",
    )
    body = html.split("<body", 1)[1]
    assert "<h1>表題</h1>" in body
    assert "<strong>重要</strong>" in body
    assert '<div class="admonition note">' in body
    assert "<li>項目1</li>" in body


def test_asciidoc_format_composes_with_ruby_and_bouten():
    """AsciiDoc本文でもwashi独自のふりがな({漢字|かんじ})・傍点
    ([対象]{.class})記法がそのまま使える(AsciiDoc自体には無い構文)。"""
    pytest.importorskip("pyasciidoc")
    html = render("吾輩は{猫|ねこ}である。[名前]{.sesame_dot}はまだ無い。",
                  format="asciidoc")
    assert "<ruby>猫<rp>(</rp><rt>ねこ</rt><rp>)</rp></ruby>" in html
    assert '<em class="sesame_dot">名前</em>' in html


def test_asciidoc_format_works_with_vertical_and_genko():
    pytest.importorskip("pyasciidoc")
    html = render("= 表題\n\n本文。\n", format="asciidoc",
                  vertical=True, genko=True)
    body = html.split("<body", 1)[1]
    assert 'class="vertical genko"' in html
    assert '<span class="cell">本</span>' in body


def test_unknown_format_raises_value_error():
    with pytest.raises(ValueError, match="markdown"):
        render("text", format="not-a-real-format")


def test_asciidoc_format_without_pyasciidoc_raises_clear_error(monkeypatch):
    """pyasciidoc未導入でformat='asciidoc'を使うと分かりやすいエラーに
    なる(黙ってMarkdownとして解釈したりしない)。"""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *a, **kw):
        if name == "pyasciidoc":
            raise ImportError("pyasciidoc not installed (test)")
        return real_import(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(ValueError, match="pyasciidoc"):
        render("= 表題\n", format="asciidoc")


# ---- 縦書き/原稿用紙 × [.form]: フォーム定義JSONを壊さない ----

import json  # noqa: E402

_FORM_DOC = (
    "本文!!\n\n[.form]\n"
    '{"action":"https://w.example/submit","fields":'
    '[{"name":"n","label":"名前!?","type":"text","maxlength":20}]}\n'
)


def _form_json(html):
    m = re.search(
        r'<script type="application/json">(.*?)</script>', html, re.DOTALL)
    assert m, "フォーム定義の <script> が見つからない"
    return json.loads(m.group(1))


def test_vertical_form_json_survives_tcy():
    """縦中横(<span class="tcy">)が <script> 内のJSONに刺さらない。"""
    schema = _form_json(render(_FORM_DOC, vertical=True))
    assert schema["fields"][0]["maxlength"] == 20
    assert schema["fields"][0]["label"] == "名前!?"


def test_vertical_tcy_still_applies_to_prose_when_form_present():
    html = render(_FORM_DOC, vertical=True)
    assert '<span class="tcy">!!</span>' in html


def test_genko_form_json_survives_cell_wrapping():
    """1字1マス(<span class="cell">)と &quot; 化が <script> 内に及ばない。"""
    schema = _form_json(render(_FORM_DOC, genko=True))
    assert schema["fields"][0]["maxlength"] == 20


def test_tcy_leaves_character_references_alone():
    """素通しHTML中の文字参照(&#39;等)を分解しない。"""
    assert _tcy("&#39;12&#39;") == '&#39;<span class="tcy">12</span>&#39;'


# ---- asciidoc format: 生HTMLブロックを素通ししない ----


def test_asciidoc_format_does_not_pass_raw_html_blocks():
    html = render("<script>alert(1)</script>\n\n本文。\n", format="asciidoc")
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


# ---- [.form] が段落直後(空行なし)でも効く(markdown入力) ----


def test_form_block_can_interrupt_a_paragraph_in_markdown():
    html = render('前の段落\n[.form]\n{"action":"/s","fields":[]}\n')
    assert 'class="fr-form"' in html


# ---- to_pdf: Chrome不在は SystemExit ではなく RuntimeError ----


def test_to_pdf_raises_runtime_error_without_chrome(monkeypatch, tmp_path):
    monkeypatch.setattr(pywashi.shutil, "which", lambda c: None)
    with pytest.raises(RuntimeError, match="Chrome"):
        pywashi.to_pdf(tmp_path / "a.html", tmp_path / "a.pdf")


# ---- frontmatter: CRLF改行でも認識する ----


def test_frontmatter_accepts_crlf():
    html = render("---\r\ntitle: 表題\r\nauthor: 著者\r\n---\r\n本文。\r\n")
    assert "<h1>表題</h1>" in html
    assert "title:" not in html.split("<body")[1]
