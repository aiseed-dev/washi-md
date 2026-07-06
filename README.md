# washi-md

Markdown から**美しい日本語文書** (HTML / PDF) を作るコマンド。

```bash
pip install washi-md

washi report.md          # → report.html (組版済み・自己完結・1ファイル)
washi report.md --pdf    # → report.pdf も出力 (Chrome/Chromium ヘッドレス印刷)
```

## なにが「綺麗」になるか

- **フォントは モリサワUD を最優先**: 商用の UD黎ミン/UD新ゴ (Morisawa Fonts)
  がインストールされていればそれを使い、無ければ BIZ UD → ヒラギノ/Noto の順で
  フォールバック。`--embed-fonts DIR` で BIZ UD の woff2 (SIL OFL) を HTML に
  埋め込めば、フォントの無い相手の環境でも同じ見た目になる
- **日本語組版CSS を同梱**: 本文は明朝・両端揃え・段落頭一字下げ・行間1.9、
  見出しはゴシック、行頭禁則 (`line-break: strict`)、約物の行頭詰め
  (`text-spacing-trim`)、句読点のぶら下げ
- **CJKフレンドリーな Markdown 解釈**
  ([mdit-py-cjk-friendly](https://github.com/aiseed-dev/mdit-py-cjk-friendly)):
  文中改行が空白にならない・全角括弧に隣接した強調が効く
- **印刷/PDF対応**: `@page` で A4・余白・ページ番号。表・コード・見出しの
  ページまたぎを抑止。`--pdf` は Chrome ヘッドレスで生成 (追加依存なし)
- frontmatter (`title` / `author` / `date`) から表題部を生成

## 使い方

```
washi INPUT.md [-o OUTPUT.html] [--title 表題] [--pdf] [--embed-fonts DIR]
      [--theme default|textbook|gothic] [--css FILE ...] [--no-base-css]

```

Python から:

```python
from washi_md import render
html = render(markdown_text, title="報告書")
```

## テーマとカスタムCSS

- `--theme textbook` — 本文を**UDデジタル教科書体**に (学習教材向け。行間2.0)
- `--theme gothic` — 本文ゴシック・字下げなし (ビジネス文書・報告書風)
- `--css my.css` — 自分のCSSを同梱CSSの後に追加 (自分のルールが優先。繰り返し可)
- `--no-base-css` — 同梱CSSを使わず完全に自分のCSSで組む

```python
from washi_md import render
html = render(md_text, theme="textbook", extra_css=[Path("my.css")])
```

## ロードマップ

- docx 出力 (美しい日本語 reference-doc)
- AI が出力した Markdown の整形 (フォーマッタ)

## License

MIT
