## 薄い縦切り一本分の見通し（スマホ先行）

### 0. 現状（リポジトリの実装状況）
- Python の最小アプリ `keep_backup.app` が存在する
  - `--mode backup` は `backups/YYYY-MM-DD/keep.json` にダミー1件を書き、ログと stdout の summary を出す
  - `--mode smoke-playwright` は **ログイン無し**の Chromium 起動確認（Google Keep を開けるか）だけを行う
- `backup_keep.bat` / `docker compose` など入口の整備は未着手
- ログイン済みブラウザプロファイルの運用は未実装（CI 用の無ログイン smoke が先行）

> このドキュメントは「スマホだけで進められる範囲を先に固める」ための実行プロンプトとして、未着手点と次の最短ステップを明示する。

### 1. この一本で“通す”こと（スマホ先行の最小成功パス）
- **スマホだけ**で進められる範囲に限定する（PC/WSL/Docker は後回し）
- Google Keep アプリで見えているノート本文を少数取得し、`keep.json` のフォーマットに落とし込む
  - 取得は**手作業でよい**（まずはフォーマットと運用手順を確定する）
- `backups/YYYY-MM-DD/keep.json` の構造と保存場所を確定する
- `logs/run_YYYY-MM-DD_HHMMSS.log` の最小ログ項目を確定する（内容だけ合意すればよい）
- stdout の summary 1行フォーマットを確定する（内容だけ合意すればよい）

> 目的：PC が無くても「何を/どこに/どう残すか」を決め切る。実装は後工程でよい。

—

### 2. 意図的に捨てるもの（今回の薄さの核心）
- 全件取得（スクロールで無限に読み込む処理はやらない）
- アーカイブ／ゴミ箱の取得
- チェックリスト構造、ラベル等の付随要素
- 自動ログイン（認証フローはコードで書かない）
- 保持ポリシー（古いバックアップ削除）
- HTML生成やGoogle Docs化
- PC/WSL/Docker 上での Playwright 実行（後工程に送る）

—

### 3. 出力は JSON 1ファイルだけ（壊れにくい最小構造）
- 出力先：`backups/YYYY-MM-DD/keep.json`
- 形式は最小限で固定
  - `scraped_at`（実行日時）
  - `notes`（配列）
    - 各要素は `body`（本文テキスト）だけでもよい
- 失敗情報はログに寄せ、JSONに無理に詰めない（薄い縦切りなので）

—

### 4. ログは“運用の最低限”だけ（内容合意を先に）
- 出力先：`logs/run_YYYY-MM-DD_HHMMSS.log`
- 書く内容（最低限）
  - 開始時刻 / 終了時刻
  - 成功 or 失敗（終了コード）
  - 取得件数
  - 出力ディレクトリ
  - 所要時間
  - 失敗時の例外メッセージ（あれば）

### 4.5. stdout は CI 互換の最小要約のみ（内容合意を先に）
- 1 行目に summary を固定フォーマットで出す
  - 例：`summary success=true notes_count=3 duration_seconds=4.20 output=backups/YYYY-MM-DD/keep.json`
- 失敗時は 2 行目以降で `error=...` を出す
  - ログ詳細はログファイルに寄せる

—

### 5. 次フェーズ（PC/WSL/Docker で実装する内容）
- Windows で `backup_keep.bat` をダブルクリック（入口は作る）
- WSL(Ubuntu) 上で Docker コンテナを起動（入口は作る）
- コンテナ内の Playwright が **ログイン済みブラウザプロファイル**を使って Google Keep を開く（要実装）
- 画面に見えている範囲だけでいいので、ノート本文を少数取得して `keep.json` に保存（要実装）
- 1本のログファイルに「成功/失敗・取得件数・出力先・所要時間」を残して終了
- stdout にも同じ最小要約を出す（CI 互換）

> スマホフェーズで確定した JSON/ログ/summary の仕様に合わせて実装する。

—

### 6. この一本の完了条件（Done）
- スマホだけで `keep.json` の最小フォーマットと保存場所が合意できている
- ログと stdout summary の**内容**が合意できている（実装は次フェーズでよい）
- 次フェーズの入口（Windows/WSL/Docker）に渡す仕様が揃っている

> ここまで到達したら勝ち。次のステップで PC/WSL/Docker 実装に移行する。
