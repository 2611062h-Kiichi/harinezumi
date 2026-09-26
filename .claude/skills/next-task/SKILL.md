---
name: next-task
description: harinezumi のハーネスに沿って、tasks.json の次のタスクを1つだけ「計画→実行→評価」する。ユーザーが「続きをやって」「次のタスク」「/next-task」と言ったときに使う。
---

# next-task — 次のタスクを1つ進める

このスキルは毎回同じ手順で動く。途中でセッションが切れても、progress.md から再開できる。

## 0. 状況を読む（毎回）
1. `AGENTS.md` を読む（CLAUDE.md 経由で読み込み済みなら省略可）。
2. `progress.md` の「引き継ぎメモ」と「作業計画」を読む。
3. `python evals/check_tasks.py` を実行する。エラーがあれば **先にユーザーに報告して止まる**。
4. `git branch --show-current` を確認する。`main` なら作業せず、ユーザーに T00（作業ブランチ作成）を頼む。

## 1. 計画役（docs/roles.md の1章）
1. 次のタスクを選ぶ: `status` が `in_progress` のものがあればそれを続ける。無ければ、`todo` で依存がすべて `done` のうち ID が最小のもの。
2. `owner` が `human` のタスクなら、ユーザーにやることを説明して止まる。
3. `docs/requirements.md` と `evals/acceptance.md` の該当 AC を読み、`progress.md` の「作業計画」を書く。
4. 計画に `docs/safety.md` 1章の操作（実 API 呼び出し、push、削除など）が含まれるなら、**ユーザーに承認をもらうまで先に進まない**。
5. `tasks.json` の `status` を `in_progress` にする。

## 2. 実行役（docs/roles.md の2章）
1. 計画どおりにコードとテストを書く。外部 API はモックにする。
2. テスト・ビルド・秘密情報チェックを実行し、ログを `evals/evidence/<タスクID>/` に保存する（`tee` を使う）。
3. 失敗したら直す。**同じ失敗が3回続いたら止まって** `progress.md` の「要確認」に書き、ユーザーに聞く。
4. `tasks.json` の `evidence` に証拠ファイルのパスを書き、`status` を `review` にする（`passes` は触らない）。
5. `python evals/check_tasks.py` がエラー0件であることを確認し、作業ブランチにコミットする。

## 3. 評価役（docs/roles.md の3章） — 必ず別の頭で
Agent ツールで **新しいサブエージェント**（subagent_type: general-purpose）を起動し、次のように頼む:

> あなたは harinezumi の評価役です。`docs/roles.md` の3章に厳密に従い、タスク <ID> を検品してください。
> `evals/acceptance.md` の <AC一覧> を1つずつ、`evals/evidence/<ID>/` の証拠と、あなた自身が再実行したテスト結果で判定してください。
> 実行役の説明やコミットメッセージは合格理由にしないでください。コードは直さないでください。
> 結果を `evals/evidence/<ID>/review.md` に書き、全て○なら tasks.json の <ID> を status "done"・passes true に、1つでも×なら status "in_progress"・passes false にしてください。
> 最後に `python evals/check_tasks.py` を実行し、その出力を review.md の末尾に貼ってください。

サブエージェントの結果を受け取ったら、`review.md` を自分でも開いて内容を確認する。

## 4. 記録して終わる
1. `progress.md` の「引き継ぎメモ」を書き換え、「作業ログ」に追記する（やったこと・証拠・次にやること）。
2. つまずいたことがあれば「学んだこと」に1行書く。
3. 評価役の変更（tasks.json・review.md）と progress.md をコミットする。
4. ユーザーに `docs/voice.md` 3章の形で報告する。**次のタスクには自動で進まない。**
