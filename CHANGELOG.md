# Changelog

## 0.9.5 (2026-07-13) — AsciiDoc入力に対応

- `render(text, format="asciidoc")` / CLIの `--format asciidoc`
  （`.adoc`/`.asciidoc`拡張子は自動判定）で、AsciiDoc本文を組版できる
  ように。構文の解釈自体は別パッケージ
  [pyasciidoc](https://github.com/aiseed-dev/pyasciidoc)に委譲し、
  washiは受け取ったHTMLを従来どおり整形するだけ（見出し・強調・
  admonition・箇条書きの解釈がpyasciidoc、フォント・組版CSS・縦書き・
  原稿用紙・PDF化はすべてwashi側で変わらず適用される）。
- ふりがな({漢字|かんじ})・傍点/傍線([対象]{.class})はwashi独自の記法
  なので、AsciiDoc本文中でもそのまま使える(pyasciidoc.asciidocに加えて
  ruby/boutenプラグインを合成)。
- ヘッドレスChromeで実際に「見出し＋強調＋admonition＋箇条書き＋ふりがな」
  を含むAsciiDoc文書を縦書き・原稿用紙モードでレンダリングし、genkoの
  マス目・ルビの分離まで正しく動くことを確認。
- pyasciidoc未導入で`format="asciidoc"`を使うと分かりやすいエラーに
  なる(黙ってMarkdownとして解釈したりしない)。
- 新規オプション依存 `pywashi[asciidoc]`（`pyasciidoc>=0.3`）。
- pytest37件（新規5件）。

## 0.9.4 (2026-07-13) — パッケージ名を washi-md → pywashi に改称

- **PyPI/インポート名を `washi-md`/`washi_md` から `pywashi` に改称**
  （ユーザー指摘「"md"はmarkdownの略語のはずなので冗長」）。短い
  `washi` はPyPIで既に別プロジェクト（2018年公開・無関係な研究整理
  スクリプト）に取られていたため `pywashi` を採用。
- **CLIコマンド名は `washi` のまま変わらない**（`pip install pywashi` で
  `washi` コマンドが入る。ブランド名と配布名を分離）。
- ユーザーテーマの設定ディレクトリも `~/.config/washi-md/themes/` から
  `~/.config/pywashi/themes/` に変更（要移行）。
- 旧 `washi-md` パッケージはPyPI上に0.9.1〜0.9.3が残るが、以後の更新は
  `pywashi` 側でのみ行う。
- pytest32件（変更なし・全てpywashi名で再確認）。

## 0.9.3 (2026-07-13)

- admonition(`<div class="admonition {label}">`。pyasciidocのNOTE:/TIP:/
  IMPORTANT:/WARNING:/CAUTION:が出すマークアップ)用のCSSを追加
  （種別ごとの左罫線色+薄い背景色）。
- 原稿用紙(genko)モードでadmonitionを1マス1文字方式のマス化対象外にした
  ——ラベル+注記文というブロック構造は原稿用紙のマス目と噛み合わず、
  実際に混ぜてレンダリングするとラベルの文字までマス目に分解されて
  崩れることを確認して対応。`_genko_cells`にadmonition div内をスキップする
  ロジックを追加し、genko.cssでも横書き(writing-mode:horizontal-tb)に
  固定・平文向けdisplay:inlineリセットを打ち消すオーバーライドを追加。
- pytest32件（新規2件）。

## 0.9.2 (2026-07-13)

- 原稿用紙(`genko=True`)のマス目を作り直し: 背景CSSグラデーションでマス目を
  描く旧方式は、フォントの行送り計算と理想値がわずかに食い違い、行を追う
  ごとに文字とマス目がずれていた（実測で確認）。文字自身を1マス1マスの
  箱（`<span class="cell">`）にして枠線を引く方式に変更。ずれが原理的に
  起きなくなった。マスは`box-sizing:border-box`・開始側の枠線は各段落の
  最初のマス（`.cell:first-child`）が閉じる（二重線・折返しずれの両方を防ぐ）。
- ルビの読み（`rt`/`rp`）・`pre`/`code`/`table`の中身はマス目の対象外
  （元々の方針どおり）。
- 段落先頭に空マス1つ（字下げ）を機械的に挿入 ── `display:inline`の`<p>`には
  `text-indent`が効かない（CSS仕様上非対応）ため。CommonMark自体が地の文の
  行頭全角スペースも剥がしてしまう（markdown-itの仕様）ことが分かったため、
  この機械挿入が字下げの実体になる。
- `render()`に`author`引数を追加（既定はfrontmatterの`author:`）。今まで
  著者名を渡す手段が無く、縦書き・原稿用紙のどちらでも表示されていなかった
  （pykobo実運用で発覚）。

## 0.9.1 (2026-07-12)

- `render()` に `font_size`（基準文字サイズpx・印刷はA4縦書き24px≈40字/列を推奨）と
  `extra_style`（生CSS追記・例 `@page{size:A4 landscape}`）を追加。
  青空文庫ワープロ（pykobo 執筆タブ）の「文字が小さすぎる」実需から。

## 0.9.0 (2026-07-11)

- 傍点・傍線対応: `[テキスト]{.sesame_dot}` → `<em class="sesame_dot">` —
  mdit-py-cjk-friendly 0.3 の `bouten` プラグイン(Pandoc 風クラス付きスパン)。
  text-emphasis / text-decoration の CSS を同梱し、ゴマ点・白ゴマ・丸・三角・
  二重丸・蛇の目・ばつの傍点と、実線・二重・鎖線・破線・波線の傍線
  (上線 `overline_*` 含む)を横書き・縦書きの両方で表示できる
- 依存を mdit-py-cjk-friendly>=0.3 に更新

## 0.8.0 (2026-07-09)

- ふりがな対応: `{漢字|かんじ}`(グループルビ)・`{東京|とう|きょう}`(モノルビ)
  — mdit-py-cjk-friendly 0.2 の `ruby` プラグイン(でんでんマークダウン形式)。
  縦書きテーマでもそのまま使える
- 依存を mdit-py-cjk-friendly>=0.2 に更新

## 0.7.0 (2026-07-07)

- `--genko`: 原稿用紙 (1字1マスのグリッド、既定20字/行)。単体で横書き、
  `--vertical` 併用で縦書き原稿用紙。半角英数は text-transform:
  full-width で全角化してマスに収める。マス目は CSS グリッド背景
  (行の枠 + マス区切りの2層 repeating-linear-gradient) で、
  グリフの半レディングに合わせて位置合わせ済み。字数は
  `--css` で `--genko-cols` を上書きして変更可

## 0.6.0 (2026-07-07)

- `--vertical`: 縦書き (writing-mode: vertical-rl)。右→左の行送り、
  1〜2桁の数字と !? ペアは縦中横 (text-combine-upright)、
  表・コードブロックは横書きのまま埋め込み。方向依存の装飾
  (見出しのアクセントバー・引用の罫線等) は論理プロパティで自動変換。
  画面は横スクロール、PDF は右綴じの書籍式ページ送り
- pyproject.toml を復元 (0.3.0 以降誤って空になっていた)

## 0.5.0 (2026-07-07)

- `--font-serif NAME` / `--font-sans NAME`: インストール済みフォントを名前で
  直接指定 (Morisawa Fonts の Select 8 等の商用書体がCSSなしで使える)
- ユーザーテーマ: ~/.config/washi-md/themes/*.css を --theme で利用可能に
  (同梱テーマより優先。テーマ一覧・エラー表示にも反映)

## 0.4.0 (2026-07-07)

- テーマ追加: maru (丸ゴシック/Zen Maru Gothic、●見出し)・
  bungei (オールド明朝/Shippori Mincho、行間2.05)
- `--webfonts`: テーマCSSの @webfonts: 宣言から Google Fonts の<link>を注入。
  フォント未導入の環境・PDF生成でもテーマ書体が使える (要ネットワーク)

## 0.3.0 (2026-07-07)

- `--theme`: 用途別プリセット (default=明朝 / textbook=UDデジタル教科書体 /
  gothic=ゴシック本文)。テーマはフォント変数中心の小さなCSSで、追加も容易
- `--css FILE`: ユーザーCSSを同梱CSSの後に追加 (繰り返し指定可)
- `--no-base-css`: 同梱CSSを使わない
- Python API: render(theme=, extra_css=, base_css=)

## 0.2.0 (2026-07-07)

- フォントスタックを モリサワUD最優先に: UD黎ミン/UD新ゴ (Morisawa Fonts、
  インストール時のみ) → BIZ UD → ヒラギノ/Noto
- `--embed-fonts DIR`: BIZ UD の woff2 (SIL OFL) を data URI で自己完結HTMLに
  埋め込み。フォント未導入の環境・配布先でも同じ組版で表示される
