# keep-backup

Google Keep ノートのバックアップを取るための、コンテナ実行前提の最小構成です。

## この README の前提
- 標準の実行主体は **Docker / docker compose** です。
- `make` は `docker compose ...` の薄いラッパとして使います（運用しやすい別名ターゲットを含む）。
- `uv run ...` の直実行は一時検証向けで、通常運用の入口にはしません。

## 推奨コマンド（通常運用）

```bash
make docker-up
make smoke
make smoke-login
make smoke-fixture
make backup
make docker-down
```

短い別名でも同じ操作が可能です（すべて同じ Docker 実行に委譲）。

```bash
make up
make smoke
make login
make probe
make dom
make fixture
make run
make parse-dom
make down
```

使えるターゲット一覧は `make help` で確認できます。

## 初回セットアップ〜実行（迷わない手順）

リポジトリ直下で次を順番に実行します。

```bash
cd /path/to/2026-keep-backup
cp --update=none .env.example .env
# 任意: bind mount の所有者不一致を避けるために、WSLユーザーIDを反映
printf "LOCAL_UID=%s\nLOCAL_GID=%s\n" "$(id -u)" "$(id -g)" >> .env
make docker-up
```

次に `.env` を開き、ログイン済みプロファイルのパスを設定します。

```env
KEEP_BROWSER_PROFILE_DIR_HOST=/home/yourname/.config/google-chrome/Profile 1
KEEP_BROWSER_PROFILE_DIR_CONTAINER=/keep-profile
```

設定後は、以下の順で動作確認すると分かりやすいです。

```bash
make smoke
make smoke-login
make smoke-fixture
make backup
```

## Docker 実行の補足
- `make docker-up` はローカル `Dockerfile` を build します。
- イメージ build 時に `uv sync --locked` を実行し、`uv.lock` を唯一の依存ソースとして同期します。
- コンテナ内コマンドは `uv run --no-sync` で実行されます。

`pyproject.toml` / `uv.lock` を更新した場合は、`make docker-up`（`--build` 付き）を再実行して、イメージ内の依存を同期してください。

## ログイン済みプロファイルの扱い
このプロジェクトでは、ログイン済み Chromium プロファイルを **外部資産** として扱います。
リポジトリ内へコピーしないでください。

### 設定
1. `.env.example` を複製して `.env` を作成

```bash
cp .env.example .env
```

2. `.env` にホスト側の絶対パスを設定
   - `KEEP_BROWSER_PROFILE_DIR_HOST`: ホスト（WSL）側プロファイルの実パス
   - `KEEP_BROWSER_PROFILE_DIR_CONTAINER`: コンテナ側マウント先（既定 `/keep-profile`）

例:

```env
KEEP_BROWSER_PROFILE_DIR_HOST=/home/yourname/.config/google-chrome/Profile 1
KEEP_BROWSER_PROFILE_DIR_CONTAINER=/keep-profile
```

### マウントの挙動
- `docker-compose.yml` では `KEEP_BROWSER_PROFILE_DIR_HOST` を bind mount のソースに使用します。
- コンテナでは `KEEP_BROWSER_PROFILE_DIR_CONTAINER` をプロファイルパスとして使用します。
- アプリには `KEEP_BROWSER_PROFILE_DIR` としてコンテナ側パスを渡すため、WSL と Docker のパス差分を意識せず実行できます。
- さらに `LOCAL_UID` / `LOCAL_GID` を指定すると、コンテナ実行ユーザーを WSL 側と揃えられます（`/app` の権限衝突回避）。

### 注意
- `.env` は gitignore 対象です。コミットしないでください。
- CI では `KEEP_BROWSER_PROFILE_DIR` / `KEEP_BROWSER_PROFILE_DIR_HOST` を未設定のまま実行し、プロファイル非依存で検証します。

## 実行モード

### 1) スモーク（プロファイル不要）

```bash
make smoke
```

Chromium の起動と Google Keep への到達を確認し、CI で利用しやすい要約行を出力します。

### 2) スモーク（ログイン必須）

```bash
make smoke-login
```

以下のいずれかに該当すると失敗します。
- `https://accounts.google.com/...` へリダイレクトされた
- 最終URLが `https://keep.google.com/...` 以外だった

### 3) スモークプローブ（ログイン + DOM確認）

```bash
make smoke-probe
```

ログイン状態チェックに加えて、Keep のノート要素
`[aria-label="Notes"] [role="listitem"]` が 1 件以上存在するかを検証します。

また、端末出力を `logs/smoke_probe_latest.txt` に保存し、終了時に
`codex_context_file=...` を出力します（`logs/` に書き込めない場合は `/tmp/keep-backup-smoke-probe-*.txt` にフォールバック）。

さらに実行後に、最新の `logs/run_*.log` の末尾 20 行を transcript に追記します。

### 4) DOMスナップショット付きスモーク（ログイン + DOM確認 + HTML保存）

```bash
make smoke-dom
```

`smoke-probe` と同じログイン/要素検証を行ったうえで、ページ HTML を
`logs/artifacts/dom_snapshot_*.html` に保存します。

`backup` 実行（Keep本番取得）でも同様に DOM スナップショットを保存します。

- 取得サイズはデバッグ用途として最大 200,000 文字に制限（大きすぎる出力を防止）
- summary の `output=` に保存先が出るため、CI や手元で追跡しやすい

### 5) backup 実行（Keep取得 / 手入力どちらも可）

入力を指定しない場合、ログイン済みプロファイルを使って Keep からノートを取得します。

```bash
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode backup
```

手入力ノートで動作確認したい場合は、従来どおり `--note` / `--notes-file` も使えます。

```bash
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode backup --note "買い物メモ" --note "次の会議アジェンダ"
```

```bash
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode backup --notes-file notes.txt
```


### 6) 保存済みDOMの再解析（parse-dom）

```bash
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode parse-dom
```

既定では最新の `logs/artifacts/dom_snapshot_*.html` を入力として読み取り、
`backups/YYYY-MM-DD/keep_from_dom.json` を出力します。

入力/出力を明示したい場合は次のオプションを使います。

```bash
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode parse-dom \
  --dom-input logs/artifacts/dom_snapshot_2026-01-01_120000.html \
  --dom-output backups/2026-01-01/keep_from_dom.json
```

## 実行時依存ポリシー
実行時依存は `pyproject.toml` と `uv.lock` で宣言・固定します。

- Playwright（Python パッケージ）は通常の実行時依存に含める
- `uv run --with ...` は一時検証用途に限定する
- ブラウザバイナリは環境準備として別途導入（`uv run playwright install chromium`）
- Docker image build でも `uv sync --locked` による lock 同期を行う

## CI 向け要約出力
アプリは CI 連携しやすい最小要約を stdout に出力します。

```text
summary success=true notes_count=123 duration_seconds=4.20 output=backups/2025-01-01/keep.json
```

エラー時は次の行も出力します。

```text
error=...
```

必要であれば CI 側でこれらを使って pass/fail 判定や通知を行います。

通知用シークレット例:
- `SMTP_USERNAME`: 送信元（Gmail アドレス）
- `SMTP_PASSWORD`: 16文字アプリパスワード（label: `github-actions`）
- `NOTIFY_EMAIL`: 通知先アドレス

## CI（PR）fixture smoke
`main` 向け PR では `.github/workflows/no-profile-smoke-pr.yml`
（workflow 名: `fixture-smoke-pr`）が実行されます。

この workflow で行うこと:
1. `docker compose build app` でリポジトリ `Dockerfile` を build
2. `docker compose run --rm app uv lock --check` で lock 整合性確認
3. `docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-fixture` を実行
4. stdout に `summary ... success=true` があり、`error=` が無いことを検証
5. 失敗時に `logs/run_*.log` を artifact として保存

## ローカルで CI 相当を再現

```bash
make docker-up
docker compose run --rm app uv lock --check
docker compose run --rm app uv run --no-sync python -m keep_backup.app --mode smoke-playwright-fixture
make docker-down
```

期待される stdout:
- `summary success=true ...`
- `error=...` が出ない

## 今後の追加予定
- Windows 入口バッチ `backup_keep.bat`（WSL / Docker 呼び出しのみ）
- WSL 入口（共通 `docker compose` コマンドの呼び出し）
- Keep 本番取得向けのログイン済みプロファイル運用の強化
- 標準縦切り（通常 / アーカイブ / ゴミ箱を含むフルバックアップ）
- 失敗時 artifact 収集（`logs/artifacts/`）
