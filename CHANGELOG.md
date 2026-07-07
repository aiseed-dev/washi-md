# Changelog

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
