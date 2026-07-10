# washi-md

日本語 | [English](README.en.md) | [繁體中文](README.zh-TW.md) | [한국어](README.ko.md)

Markdown から**美しい日本語文書** (HTML / PDF) を作るコマンド。
横書きのビジネス文書から、縦書きの小説、原稿用紙まで、
コマンド一つで日本語らしく組む。

```bash
# PyPI 公開までは GitHub から (依存パッケージを先に):
pip install "mdit-py-cjk-friendly @ git+https://github.com/aiseed-dev/mdit-py-cjk-friendly.git"
pip install "washi-md @ git+https://github.com/aiseed-dev/washi-md.git"
# PyPI 公開後: pip install washi-md

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
- **縦書きと原稿用紙**: `--vertical` で右→左の縦組 (縦中横つき)、
  `--genko` で1字1マスの原稿用紙 (縦横両対応)
- **ふりがな**: `{漢字|かんじ}` (グループルビ)・`{東京|とう|きょう}` (モノルビ)
  — でんでんマークダウン形式。縦書きでもそのまま効く
- frontmatter (`title` / `author` / `date`) から表題部を生成

## 使い方

```
washi INPUT.md [-o OUTPUT.html] [--title 表題] [--pdf]
      [--theme default|textbook|gothic|maru|bungei]
      [--vertical] [--genko]
      [--font-serif NAME] [--font-sans NAME] [--webfonts]
      [--css FILE ...] [--no-base-css] [--embed-fonts DIR]
```

Python から:

```python
from washi_md import render
html = render(markdown_text, title="報告書")
```

## 縦書き

```bash
washi 小説.md --vertical --theme bungei --pdf
```

`--vertical` で本文が縦書き (右→左) になる。1〜2桁の数字は自動で
縦中横、表とコードブロックは横書きのまま埋め込まれる。
bungei テーマと組み合わせると小説・随筆向けの組版になる。

原稿用紙にもできる (縦横どちらでも):

```bash
washi 作文.md --genko --pdf              # 横書き原稿用紙
washi 作文.md --genko --vertical --pdf   # 縦書き原稿用紙 (20字/行)
```

1字1マスのグリッドに全角ベタ組で流し込む。半角英数は自動で全角化。
字数を変えるには `--css` で `body.genko { --genko-cols: 25; }` を渡す。

## テーマとカスタムCSS

- `--theme textbook` — 本文を**UDデジタル教科書体**に (学習教材向け。行間2.0)
- `--theme gothic` — 本文ゴシック・字下げなし (ビジネス文書・報告書風)
- `--theme maru` — **丸ゴシック** (Zen Maru Gothic。お知らせ・案内文のやわらかい文書)
- `--theme bungei` — **オールド明朝** (Shippori Mincho。文芸・随筆の趣)
- `--webfonts` — Google Fonts を読み込み、**フォント未導入の環境でも**テーマの
  書体で表示 (BIZ UD も Google Fonts にあるため default テーマにも効く。
  オフラインでは効かないので、自己完結にしたい場合は `--embed-fonts` を使う)
- `--font-serif "A1明朝"` / `--font-sans "新ゴ M"` — **インストール済みフォントを
  名前で直接指定**。Morisawa Fonts (Select 8 等) で入れた書体がCSSなしで使える。
  PDF生成もローカルレンダリングなのでそのまま効く
- **ユーザーテーマ**: `~/.config/washi-md/themes/○○.css` に置くと
  `--theme ○○` で使える (同名なら同梱テーマより優先)。お気に入りの
  書体構成を場面別に保存しておける
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
