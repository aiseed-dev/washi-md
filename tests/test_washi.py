"""washi-md の検査。

render(Markdown→自己完結HTML)を厚く、CLI(main)は一巡だけ。
PDF(Chrome ヘッドレス)は環境依存のため Chrome がある場合のみ実行。
"""
import re
import sys
from pathlib import Path

import pytest

import washi_md
from washi_md import _find_chrome, _tcy, render, themes


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
    washi_md.main()
    out_path = tmp_path / "doc.html"
    assert out_path.exists()
    assert "<h1>T</h1>" in out_path.read_text(encoding="utf-8")
    assert str(out_path) in capsys.readouterr().out


def test_cli_output_and_title(tmp_path, monkeypatch):
    src = tmp_path / "in.md"
    src.write_text("本文。\n", encoding="utf-8")
    dst = tmp_path / "out.html"
    monkeypatch.setattr(sys, "argv", ["washi", str(src), "-o", str(dst), "--title", "表題"])
    washi_md.main()
    assert "<title>表題</title>" in dst.read_text(encoding="utf-8")


# ---- PDF(Chrome がある環境のみ)----


@pytest.mark.skipif(_find_chrome() is None, reason="Chrome/Chromium なし")
def test_pdf(tmp_path, monkeypatch):
    src = tmp_path / "doc.md"
    src.write_text("# PDF テスト\n\n本文。\n", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["washi", str(src), "--pdf"])
    washi_md.main()
    pdf = tmp_path / "doc.pdf"
    assert pdf.exists()
    assert pdf.read_bytes()[:5] == b"%PDF-"
