# washi-md

[日本語](README.md) | [English](README.en.md) | 繁體中文 | [한국어](README.ko.md)

把 Markdown 變成**排版精美的日文文件** (HTML / PDF) 的指令工具。
從橫排的商務文件、直排的小說，到稿紙格式，一個指令搞定。
(以日文排版為主，但直排與稿紙同樣適用於中文文件。)

```bash
# PyPI 發佈前，請從 GitHub 安裝 (先裝相依套件):
pip install "mdit-py-cjk-friendly @ git+https://github.com/aiseed-dev/mdit-py-cjk-friendly.git"
pip install "washi-md @ git+https://github.com/aiseed-dev/washi-md.git"
# PyPI 發佈後: pip install washi-md

washi report.md          # → report.html (已排版、自我完備的單一檔案)
washi report.md --pdf    # → 另外輸出 report.pdf (Chrome/Chromium 無頭列印)
```

## 哪些地方變「精美」

- **優先使用森澤 (Morisawa) UD 字型**: 若已安裝商用的 UD黎ミン/UD新ゴ
  (Morisawa Fonts) 就直接使用，否則依 BIZ UD → ヒラギノ/Noto 的順序後備。
  `--embed-fonts DIR` 可將 BIZ UD 的 woff2 (SIL OFL) 內嵌進 HTML，
  在沒有字型的環境也能呈現相同外觀
- **內建日文排版 CSS**: 內文明體、左右對齊、段首縮排、行距 1.9、
  標題黑體、避頭尾 (`line-break: strict`)、標點擠壓
  (`text-spacing-trim`)、標點懸掛
- **CJK 友善的 Markdown 剖析**
  ([mdit-py-cjk-friendly](https://github.com/aiseed-dev/mdit-py-cjk-friendly)):
  句中換行不會變成空格、全形括號旁的強調正常生效
- **直排與稿紙**: `--vertical` 直排 (由右至左，含直排內橫排)、
  `--genko` 一字一格的稿紙 (直橫皆可)
- **列印/PDF 支援**: `@page` 設定 A4、邊界、頁碼。避免表格、程式碼、
  標題被分頁切開。`--pdf` 用無頭 Chrome 產生 (無額外相依)
- **注音／振假名(ruby)**: `{漢字|かんじ}` (群組 ruby)・`{東京|とう|きょう}`
  (逐字 ruby) — 電電 Markdown 記法,直排也直接生效
- **著重號／著重線**: `[文字]{.sesame_dot}` (Pandoc 風格類別 span) —
  內建芝麻點、圓點、三角、雙圈、蛇目、叉號著重號與實線〜波浪線著重線的
  CSS,直橫排皆支援
- 從 frontmatter (`title` / `author` / `date`) 產生標題區

## 用法

```
washi INPUT.md [-o OUTPUT.html] [--title 標題] [--pdf]
      [--theme default|textbook|gothic|maru|bungei]
      [--vertical] [--genko]
      [--font-serif 名稱] [--font-sans 名稱] [--webfonts]
      [--css FILE ...] [--no-base-css] [--embed-fonts DIR]
```

從 Python 使用:

```python
from washi_md import render
html = render(markdown_text, title="報告")
```

## 直排 (縱書)

```bash
washi novel.md --vertical --theme bungei --pdf
```

`--vertical` 讓內文直排 (行由右至左)。一到兩位數的數字自動以
直排內橫排正立顯示；表格與程式碼區塊維持橫排嵌入。
搭配 bungei 主題即為小說、散文的版面。

也可以排成稿紙 (直橫皆可):

```bash
washi essay.md --genko --pdf              # 橫排稿紙
washi essay.md --genko --vertical --pdf   # 直排稿紙 (每行20字)
```

一字一格、全形密排；半形英數字自動轉為全形。
要改每行字數，用 `--css` 傳入 `body.genko { --genko-cols: 25; }`。

## 主題與自訂 CSS

- `--theme textbook` — 內文使用 UD 數位教科書體 (學習教材，行距 2.0)
- `--theme gothic` — 內文黑體、無縮排 (商務文件、報告風)
- `--theme maru` — 圓體 (Zen Maru Gothic，柔和的通知、指南)
- `--theme bungei` — 舊式明體 (Shippori Mincho，文藝風格)
- `--webfonts` — 載入 Google Fonts，讓沒裝字型的環境也能顯示主題書體
- `--font-serif "A1明朝"` / `--font-sans "新ゴ M"` — 直接以名稱指定
  已安裝的字型 (Morisawa Fonts 等)，PDF 也同樣生效
- 使用者主題: 放到 `~/.config/washi-md/themes/名稱.css` 即可用
  `--theme 名稱` 呼叫
- `--css my.css` — 追加自己的 CSS；`--no-base-css` — 完全自訂

## 授權條款

MIT
