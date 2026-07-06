# washi-md

Markdown から**美しい日本語文書** (HTML / PDF) を作るコマンド。

```bash
pip install washi-md

washi report.md          # → report.html (組版済み・自己完結・1ファイル)
washi report.md --pdf    # → report.pdf も出力 (Chrome/Chromium ヘッドレス印刷)
```

## なにが「綺麗」になるか

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
washi INPUT.md [-o OUTPUT.html] [--title 表題] [--pdf]
```

Python から:

```python
from washi_md import render
html = render(markdown_text, title="報告書")
```

## ロードマップ

- docx 出力 (美しい日本語 reference-doc)
- AI が出力した Markdown の整形 (フォーマッタ)

## License

MIT
