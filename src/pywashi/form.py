"""form — markdown-it-py プラグイン: ``[.form]`` ブロック → 対話的フォームのマウント。

    MarkdownIt().use(form)

pywashi/pyasciidoc の ``.use(ruby).use(bouten)`` と同じ、opt-in プラグイン。
``[.form]`` の直後の行（空行まで）を **フォーム定義 JSON として「生」で捕まえ**
（インライン解析しない — JSON を壊さないため）、次を出力する:

    <div class="fr-form"><script type="application/json">…schema…</script></div>

実行時に ``form-render.js`` が ``.fr-form`` を対話的フォームに描く。この分離で、
**静的な文書組版（pywashi）と、対話的フォームが混ざらない**。定義の著述は
フォームビルダー（JSON を出力）が担い、本文中は ``[.form]`` で参照するだけ。

記法（AsciiDoc 本文中）::

    [.form]
    {"action":"https://<worker>/submit","sitekey":"0x…","confirm":true,
     "fields":[{"name":"your-name","label":"お名前","type":"text","required":true}]}

pyasciidoc の総称ロール ``[.name]`` より前に置き ``[.form]`` を横取りするので、
他のロール（``[.note]`` 等）は従来どおり ``<div class="…">`` になる。
"""

from __future__ import annotations

import json
import re

from markdown_it import MarkdownIt
from markdown_it.rules_block.state_block import StateBlock

__all__ = ["form"]

_FORM_MARK_RE = re.compile(r"^\[\.form\][ \t]*$")


def _form_rule(state: StateBlock, startLine: int, endLine: int, silent: bool) -> bool:
    pos = state.bMarks[startLine] + state.tShift[startLine]
    maximum = state.eMarks[startLine]
    if not _FORM_MARK_RE.match(state.src[pos:maximum]):
        return False

    nextLine = startLine + 1
    if nextLine >= state.lineMax or state.isEmpty(nextLine):
        return False  # 定義本体が無ければ [.form] 行として扱わない（誤爆防止）
    if silent:
        return True

    lines = []
    while nextLine < state.lineMax and not state.isEmpty(nextLine):
        p = state.bMarks[nextLine] + state.tShift[nextLine]
        mx = state.eMarks[nextLine]
        lines.append(state.src[p:mx])
        nextLine += 1

    token = state.push("form", "", 0)
    token.content = "\n".join(lines).strip()   # 生の JSON（インライン解析しない）
    token.map = [startLine, nextLine]
    token.block = True
    state.line = nextLine
    return True


def _render_form(renderer, tokens, idx, options, env) -> str:
    raw = tokens[idx].content
    try:
        schema = json.loads(raw)
    except json.JSONDecodeError as exc:
        # 著述時に気づけるよう、壊れた JSON はエラー表示に落とす（黙って消さない）
        return f'<div class="fr-form-error">フォーム定義のJSONが不正です: {exc}</div>\n'
    # "<" をエスケープして </script> 注入を防ぎ、<script> に安全に埋める
    payload = json.dumps(schema, ensure_ascii=False).replace("<", "\\u003c")
    return (
        '<div class="fr-form">'
        f'<script type="application/json">{payload}</script>'
        "</div>\n"
    )


def form(md: MarkdownIt) -> None:
    """``MarkdownIt().use(form)`` — ``[.form]`` ブロックを、対話的フォームのマウントに。"""
    # pyasciidoc の総称ロール（ad_role_block）より前に置き [.form] を横取りする。
    # markdown 入力（pyasciidoc 無し）では paragraph の前に置く。
    # alt=["paragraph"] は必須 —— これが無いと段落を消費中の paragraph
    # ルールが [.form] を「段落を終わらせる構文」と認識せず、直前に空行の
    # 無い [.form] が地の文に飲み込まれてフォームが出ない（markdown-it-py
    # 本体の heading 等が同じ option を持つのと同じ理由。asciidoc 入力では
    # ad_role_block 側の alt に相乗りして偶々動いていたが、markdown 入力
    # では動かなかった）。
    para_alt = {"alt": ["paragraph"]}
    try:
        md.block.ruler.before("ad_role_block", "cjk_form", _form_rule, para_alt)
    except KeyError:
        md.block.ruler.before("paragraph", "cjk_form", _form_rule, para_alt)
    md.add_render_rule("form", _render_form)
