# リリース手順（PyPIへの公開）

公開は**タグの push だけ**で完了する。GitHub Actions
（`.github/workflows/publish.yml`）が Trusted Publishing（OIDC）で
PyPI にアップロードするため、手元での build / twine は不要。

## 手順

```bash
# 1. バージョンを上げる ── 定義箇所はここだけ
#    （pyproject.toml は dynamic version。実体は __init__.py の __version__）
vi src/pywashi/__init__.py      # __version__ = "X.Y.Z"

# 2. CHANGELOG.md に節を書く
#    ## X.Y.Z (日付) — 変更点

# 3. テスト
python -m pytest -q

# 4. コミットして push
git add -A
git commit -m "vX.Y.Z"
git push origin main

# 5. タグを打って push（v つき ── これが公開トリガー）
git tag vX.Y.Z
git push origin vX.Y.Z
```

## 確認

- <https://github.com/aiseed-dev/pywashi/actions> ── publish が緑になるまで1〜2分
- <https://pypi.org/project/pywashi/> ── 新バージョンが見えれば完了

## 注意

- **バージョンの実体は `src/pywashi/__init__.py` の `__version__`**。
  pyproject.toml を書き換えても効かない（`[tool.hatch.version]` 参照）。
- 同じバージョン番号は PyPI に二度上げられない。タグを打つ前に
  `python -c "import pywashi; print(pywashi.__version__)"` で確認。
- 下流（bunko の `[washi]` エクストラ等）が新機能を使うときは、
  そちらの下限ピン（`pywashi>=X.Y.Z`）も上げる。
- **改称後の初回公開前に必須の作業**（`washi-md`→`pywashi`改称・
  2026-07-13）: PyPIのTrusted PublishingはプロジェクトごとにGitHub
  リポジトリ・ワークフローファイル名を紐付ける設定なので、旧
  `washi-md` プロジェクトの設定は新しい `pywashi` プロジェクトには
  引き継がれない。<https://pypi.org/manage/project/pywashi/settings/publishing/>
  （初回は「pending publisher」としてプロジェクト作成前でも登録可）で
  GitHub owner=`aiseed-dev`、repository=`pywashi`、workflow=`publish.yml`、
  environment=`pypi` を新規登録してから、初回のタグpushを行うこと。
  GitHubリポジトリ自体も `aiseed-dev/washi-md` から `aiseed-dev/pywashi`
  へリネーム（またはリポジトリ名だけ変えず中身をこの名前に更新)が必要。
