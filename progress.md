# progress.md — 途中経過と引き継ぎ

> AI はこのファイルに **追記** する（過去の記録は消さない）。
> セッションが切れても、別の AI に移っても、ここを読めば続きから再開できるように書く。

---

## 引き継ぎメモ（常に最新の状態に書き換える欄）
- **最終更新**: 2026-09-26
- **今の作業ブランチ**: `main`（まだ作業ブランチ無し）
- **最後に終わったこと**: ハーネス一式の作成（未コミット）
- **次にやること**: T00（人間）→ T01（人間）と T02（AI）
- **止まっていること / 人間待ち**: T00・T01 の人間の確認
- **注意**: `backend/.venv` と `frontend/node_modules` は main の依存で作成済み。土台ブランチ切り替え後は `pip install -r requirements.txt` と `npm install` をやり直す（typesafe-sdk, yt-dlp などが増えるため）

---

## 作業計画（計画役が書く・タスクごとに上書き）
_（まだなし）_

---

## 要確認（人間に聞きたいこと）
- docs/requirements.md 5章の Q1〜Q6

---

## 提案（AI からの変更提案。人間が採用したら該当ファイルに反映する）
_（まだなし）_

---

## 作業ログ（新しいものを下に追記）
### 2026-09-26 ハーネス作成
- 既存コード（main と origin/feature/business-contest-rubric）を調査し、docs/requirements.md 1〜2章にまとめた
- typesafe-sdk 0.7.1 のソースで Jev の入出力の型を確認した
- 作成: AGENTS.md, CLAUDE.md, docs/*, tasks.json, progress.md, evals/*, .claude/skills/next-task/SKILL.md, .claude/settings.json
- 証拠: `python evals/check_tasks.py` の結果（エラー0件）

---

## 学んだこと（改善の蓄積）
> 失敗やつまずきを1行で書く。同じ内容が **2回** 出たら、ルール化の提案を「提案」欄に書く。
> 人間が採用したら、AGENTS.md / docs/safety.md / SKILL.md のどこかに反映し、ここに「→反映済み（ファイル名）」と書く。

- （例）Windows では `python` が別の環境を指すことがある → `backend/.venv/Scripts/python` を明示する
