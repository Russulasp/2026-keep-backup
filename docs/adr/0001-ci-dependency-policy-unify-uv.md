# ADR 0001: CI の依存管理ポリシーを uv に統一する

- Status: Proposed
- Date: 2026-02-25
- Deciders: keep-backup maintainers

## Context

現状の CI は、イベント別に依存導線が分岐している。

- PR 用 (`.github/workflows/no-profile-smoke-pr.yml`)
  - `uv lock --check`
  - `uv sync --locked`
  - `uv run ...`
- main push 用 (`.github/workflows/backup-ci.yml`)
  - `python -m pip install -e .`
  - `python -m keep_backup.app ...`

`MANIFEST.md` では「実行時依存を `pyproject.toml` + `uv.lock` に固定し、`uv lock --check` と `uv sync --locked` で整合確認する」ことを明記しているため、main push 側の導線は方針と不一致になっている。

## Problem

依存導線の分岐により、次のリスクがある。

1. lock 準拠保証の差
   - PR では lock 準拠が検証されるが、main push では `pip install -e .` により lock との差分が混入し得る。
2. 再現性の低下
   - イベントにより異なる dependency resolver が走るため、同一コミットでも結果の差が出る。
3. 障害解析コストの上昇
   - 「PR では通るが main では揺れる」ケースで、依存要因の切り分けが難しくなる。

## Decision drivers

- `MANIFEST.md` の依存宣言方針と一致していること
- ローカル/CI で入口をそろえること
- lock 準拠を main 系統でも継続的に保証すること
- 既存運用（stdout 要約・通知）を壊さないこと

## Options considered

### Option A: 現状維持（PR=uv, main=pip）

- Pros
  - 変更コストがゼロ
- Cons
  - 方針不一致が継続
  - main 側の lock 乖離リスクが残る

### Option B: main push 側のみ uv 化（最小統一）

- 例
  - `astral-sh/setup-uv@v4` を追加
  - `uv lock --check`
  - `uv sync --locked`
  - `uv run python -m keep_backup.app ...`
- Pros
  - 方針不一致を短期で解消
  - main 系統でも lock 準拠保証を確保
- Cons
  - `pip install -e .` 前提の手順を更新する必要がある

### Option C: CI 共通化（再利用ワークフロー or composite action）

- 例
  - 依存セットアップを共通テンプレート化し、PR/main 両方から再利用
- Pros
  - 入口の重複定義を排除できる
  - 将来の依存更新時の修正漏れが減る
- Cons
  - Option B より初期変更コストが高い

## Recommended policy

段階導入で **B → C** を推奨する。

1. 先行して `backup-ci.yml` を uv 導線へ移行し、方針不一致を即時解消する。
2. 次に PR/main で共通の依存セットアップ手順を抽出し、CI 全体を 1 系統にする。

## Concrete acceptance criteria

- main push 用 workflow に `uv lock --check` と `uv sync --locked` が存在する
- main push 用 workflow の実行コマンドが `uv run ...` 経由である
- CI 失敗時に「lock 不整合」と「実行時エラー」がログ上で判別できる
- PR/main の双方で同じ lock 由来の依存解決が行われる

## Rollout plan (small steps)

1. `backup-ci.yml` に uv セットアップと lock 検証を追加
2. `pip install -e .` を `uv sync --locked` に置換
3. 実行コマンドを `python -m ...` から `uv run python -m ...` に置換
4. 1 週間程度、PR/main の成功率と差分障害を観測
5. 必要なら依存セットアップを共通化（Option C）

## Non-goals

- この ADR では CI の通知方式（メール送信）は変更しない
- この ADR では E2E 導入範囲は変更しない
