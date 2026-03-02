<!— docs/troubleshooting.md —>

## troubleshooting

### 1. まず確認すること
- ログイン済みプロファイルで Keep を手動で開けるか
- `logs/run_*.log` の「取得件数」が 0 になっていないか
- 出力先 `backups/YYYY-MM-DD/keep.json` が生成されているか

### 2. よくある失敗
- ログイン切れ：Keepがログイン画面になっている
  - 対処：手動でログインし直して再実行（自動ログインはしない方針）
- UI変更：要素が見つからない系のエラー
  - 対処：直近の変更点を特定し、セレクタ/導線を最小差分で直す
- タイムアウト：読み込みが遅い/待機不足
  - 対処：待機条件を強める（固定sleepより、要素待ちへ寄せる）

### 3. 追加の証跡が必要になったら
- `logs/artifacts/` にスクショを保存する運用を入れる（標準縦切り以降）
### 4. DOM調査の取り方（原因究明用）
- `make smoke-dom-investigate` を実行すると、以下を1つの転記ファイルにまとめる
  - DOMスモークの標準出力
  - 最新 `logs/run_*.log` の末尾40行
  - 最新 `logs/artifacts/dom_snapshot_*.html` のパス
- 転記ファイルは `logs/smoke_dom_investigate_latest.txt` に保存される
- `notes_count=0` の時は、まず `notes_selector` と `ready_state`、`page_url` を確認する
