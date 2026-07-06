# Changelog

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
