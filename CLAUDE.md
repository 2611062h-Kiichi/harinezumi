@AGENTS.md

# Claude 専用の追加ルール

上の AGENTS.md がすべての基本です。ここには Claude Code / Claude だけに関係するルールを足します。

## 進め方
- 作業を始めるときは `/next-task` スキル（`.claude/skills/next-task/SKILL.md`）を使う。
- 評価役は **Agent ツールで新しいサブエージェントとして起動** する。自分で書いたコードを自分の頭の中だけで合格にしない。
- 1タスク終わるごとに `python evals/check_tasks.py` を実行し、エラーが0件であることを確認してからコミットする。

## ユーザーへの話し方
- ユーザーは AI 初心者。専門用語には中学生でもわかる一言説明をつける（例:「コミット（作業のセーブポイント）」）。
- 報告は `docs/voice.md` の「ユーザーへの報告」に従う。

## ツールの使い方
- `backend/.env` は Read しない。キーが設定済みかは `python -c "from app.config import get_settings as g; print(bool(g().typesafe_api_key))"` のように **有無だけ** 確認する。
- 実際の API（Anthropic / OpenAI / TypeSafe）を呼ぶテストはお金がかかる。`docs/safety.md` の承認ルールに従う。普段のテストは偽物（モック）で行う。
- `git push`、main へのマージ、`git reset --hard` は必ずユーザーに確認してから。
- コミットメッセージの最後には、システムから指定された Co-Authored-By 行をつける。
