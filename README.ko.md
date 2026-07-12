# pywashi

[日本語](README.md) | [English](README.en.md) | [繁體中文](README.zh-TW.md) | 한국어

Markdown을 **아름답게 조판된 일본어 문서** (HTML / PDF) 로 만드는 명령어.
가로쓰기 비즈니스 문서부터 세로쓰기 소설, 원고지까지 명령 하나로 만듭니다.
(일본어 조판이 중심이지만, 세로쓰기·원고지는 한국어 문서에도 쓸 수 있습니다.)

```bash
pip install "mdit-py-cjk-friendly @ git+https://github.com/aiseed-dev/mdit-py-cjk-friendly.git"
pip install pywashi

washi report.md          # → report.html (조판 완료·자기완결·단일 파일)
washi report.md --pdf    # → report.pdf도 출력 (Chrome/Chromium 헤드리스 인쇄)
```

## 무엇이 「아름다워」지나

- **모리사와 (Morisawa) UD 글꼴 우선**: 상용 UD黎ミン/UD新ゴ (Morisawa
  Fonts) 가 설치되어 있으면 사용하고, 없으면 BIZ UD → 히라기노/Noto 순으로
  폴백. `--embed-fonts DIR` 로 BIZ UD woff2 (SIL OFL) 를 HTML에 내장하면
  글꼴이 없는 환경에서도 같은 모양이 됩니다
- **일본어 조판 CSS 내장**: 본문 명조·양쪽 정렬·단락 첫 줄 들여쓰기·행간
  1.9, 제목은 고딕, 행두 금칙 (`line-break: strict`), 문장부호 당김
  (`text-spacing-trim`), 문장부호 내어쓰기
- **CJK 친화적 Markdown 해석**
  ([mdit-py-cjk-friendly](https://github.com/aiseed-dev/mdit-py-cjk-friendly)):
  문장 중간의 줄바꿈이 공백이 되지 않고, 전각 괄호 옆의 강조가 제대로
  동작합니다
- **세로쓰기와 원고지**: `--vertical` 로 오른쪽→왼쪽 세로쓰기
  (세로쓰기 안 가로쓰기 포함), `--genko` 로 한 글자 한 칸의 원고지
  (가로·세로 모두 가능)
- **인쇄/PDF 지원**: `@page` 로 A4·여백·쪽 번호. 표·코드·제목이 페이지에
  걸쳐 잘리지 않도록 처리. `--pdf` 는 헤드리스 Chrome으로 생성 (추가 의존성
  없음)
- **후리가나(루비)**: `{漢字|かんじ}` (그룹 루비)・`{東京|とう|きょう}`
  (모노 루비) — 덴덴 마크다운 표기. 세로쓰기에서도 그대로 동작
- **방점·방선**: `[텍스트]{.sesame_dot}` (Pandoc 스타일 클래스 스팬) —
  참깨점·원·삼각·이중원·뱀눈·가위표 방점과 실선〜물결선 방선의 CSS 내장.
  가로쓰기·세로쓰기 모두 지원
- frontmatter (`title` / `author` / `date`) 에서 표제부 생성

## 사용법

```
washi INPUT.md [-o OUTPUT.html] [--title 표제] [--pdf]
      [--theme default|textbook|gothic|maru|bungei]
      [--vertical] [--genko]
      [--font-serif 이름] [--font-sans 이름] [--webfonts]
      [--css FILE ...] [--no-base-css] [--embed-fonts DIR]
```

Python에서:

```python
from pywashi import render
html = render(markdown_text, title="보고서")
```

## 세로쓰기

```bash
washi novel.md --vertical --theme bungei --pdf
```

`--vertical` 로 본문이 세로쓰기 (행이 오른쪽→왼쪽) 가 됩니다.
한두 자리 숫자는 자동으로 세로쓰기 안 가로쓰기로 바로 세워지고,
표와 코드 블록은 가로쓰기 그대로 들어갑니다. bungei 테마와 조합하면
소설·수필용 조판이 됩니다.

원고지로도 만들 수 있습니다 (가로·세로 모두):

```bash
washi essay.md --genko --pdf              # 가로쓰기 원고지
washi essay.md --genko --vertical --pdf   # 세로쓰기 원고지 (한 행 20자)
```

한 글자 한 칸의 전각 조판으로 흘려 넣습니다. 반각 영숫자는 자동으로
전각화. 행당 글자 수는 `--css` 로 `body.genko { --genko-cols: 25; }` 를
넘기면 바꿀 수 있습니다.

## 테마와 사용자 CSS

- `--theme textbook` — 본문을 UD 디지털 교과서체로 (학습 교재용, 행간 2.0)
- `--theme gothic` — 본문 고딕·들여쓰기 없음 (비즈니스 문서·보고서풍)
- `--theme maru` — 둥근 고딕 (Zen Maru Gothic, 부드러운 안내문)
- `--theme bungei` — 올드 명조 (Shippori Mincho, 문예 분위기)
- `--webfonts` — Google Fonts를 읽어 글꼴이 없는 환경에서도 테마 서체로 표시
- `--font-serif "A1明朝"` / `--font-sans "新ゴ M"` — 설치된 글꼴을 이름으로
  직접 지정 (Morisawa Fonts 등). PDF 생성에도 그대로 적용
- 사용자 테마: `~/.config/pywashi/themes/이름.css` 에 두면
  `--theme 이름` 으로 사용 가능
- `--css my.css` — 자기 CSS를 추가; `--no-base-css` — 완전히 직접 구성

## 라이선스

MIT
