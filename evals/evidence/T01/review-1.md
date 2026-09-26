# T01 検品結果（評価役）

- 日付: 2026-09-26
- 対象: tasks.json T01「【人間】docs/requirements.md 5章の未確定事項 Q1〜Q3 に回答する」
- 記録コミット: `54ef02b` Record human answers to Q1-Q3 (T01)
- 人間の回答原文（メインの AI がプロンプトに転記したもの）: 「Q1、良いです」「Q2、そうです」「Q3、僕のキーです」（Q3 は「Windows の環境変数 TYPESAFE_API_KEY が設定されていたが、あなたのキーか」という質問への返事）
- 読んだ順: `docs/roles.md` 3章 → `evals/acceptance.md` → `tasks.json` の T01 → `evals/evidence/T01/` → `git show 54ef02b` / `git diff`
- 読んでいないもの: `backend/.env`、環境変数の値（指示どおり）

## 判定: **不合格**（× が1つ）→ `status: "in_progress"`, `passes: false`

| 条件 | 判定 | 根拠 |
|---|---|---|
| AC-02 未確定事項 Q1〜Q3 に人間の回答が記録されている（AI の推測ではない） | **×** | 5章の Q1〜Q3 の記録は回答原文と一致している。ただし、回答に合わせて変えた3章の見出し `## 3. 用語の解釈 [確定・Q2]` が、Q2 で聞いていない内容まで「確定」にしている（下の「指摘1」） |
| AC-00c 秘密情報が含まれていない | ○ | 記録コミットと作業ツリーの差分で `docs/safety.md` 3章のコマンドを再実行し、何も出なかった。ただし T01 に `secret-scan.log` の証拠が無い（下の「指摘2」） |
| AC-00d `python evals/check_tasks.py` がエラー0件 | ○ | 再実行の結果「エラー 0 件 / 警告 0 件」。証拠 `check_tasks.log` と同じ結果 |

## 確認項目ごとの結果

### 1. 5章の記録が回答原文と合っているか（Q1〜Q3）→ ○
- Q1: 「**回答済み（2026-09-26、人間）:「良いです」**」→ 原文「良いです」と一致
- Q2: 「**回答済み（2026-09-26、人間）:「そうです」**」→ 原文「そうです」と一致
- Q3: 「Windows の環境変数 `TYPESAFE_API_KEY` について「僕のキーです」→ 取得済み。実通信テスト（T11）は引き続き承認制」
  - 「僕のキーです」→「取得済み」は、キーが設定済みで本人のものという回答から直接言えるので、回答の範囲内と判断した。
  - 「実通信テスト（T11）は引き続き承認制」は新しく決めたことではなく、`docs/safety.md` 1章（実際の API を呼ぶテストは承認が必要）と tasks.json の T11「【人間の承認が必要】」の再確認なので問題なし。
  - キーの値は書かれていない（変数名だけ）。
- Q4〜Q6: 「決まるまでの仮定」のまま（5固定 / 0.5 / T11 の前に人間が用意）で、確定扱いになっていない → ○

### 2. 回答に合わせて変えた他の箇所が回答の範囲内か → **×**
- 1-2節: `→ **新機能はこのブランチを土台にするのが自然** [仮定・T00 で人間が決定]` → `→ **新機能はこのブランチを土台にする** [確定・Q1]`。Q1「良いです」の範囲内 → ○
- 3章の見出し: `## 3. 用語の解釈 [仮定・T01 で人間が確認]` → `## 3. 用語の解釈 [確定・Q2]` → **×**
  - **指摘1**: 3章には2つの項目がある。
    1. 「Questions」= Jev の `questions` 引数 … Q2「そうです」で確定してよい。
    2. 「TypeSafe」= Jev の提供元 TypeSafe AI 社。**同時に「入力と出力の形（型）を決めて、形が違えばエラーにする」設計方針とも一致させる** … Q2 では聞いていない。特に後半は AI が決めた設計方針の解釈。
  - 見出しに `[確定・Q2]` を付けたことで、人間が答えていない 2 まで「人間が確定した」ように読める。これは「AI の推測を確定扱いしない」という AC-02 の条件に反する。
  - 直し方の例: 見出しの印を外し、項目ごとに印を付ける（1 に `[確定・Q2]`、2 に `[仮定]` のまま）。または 2 についても人間に確認して回答を記録する。
- 補足（不合格の理由ではない）: 5章の見出し「未確定事項（人間の回答待ち）」はそのまま。Q4〜Q6 が残っているので間違いではない。

### 3. 変更が人間の承認済み基準（`harness-baseline` タグ）に入っているか → ○
- `git rev-parse harness-baseline` = `54ef02b35d4c79b71f149e0834f4e71cb42ca995` = 記録コミット = `HEAD`
- `git tag --points-at 54ef02b` → `harness-baseline`
- `git diff 54ef02b HEAD -- docs/requirements.md` → 差分なし（コミット後に requirements.md は変わっていない）
- 注: 指摘1 を直すと requirements.md が変わるので、直したあとに人間がタグを付け直す必要がある。

### 4. 証拠と再実行の結果が一致するか → ○
- `evals/evidence/T01/requirements-diff.log` の中身と、`git show 54ef02b -- docs/requirements.md` の差分は同じ（index `b807e02..df3820a`、3か所の変更）。
- `evals/evidence/T01/check_tasks.log`「結果: エラー 0 件 / 警告 0 件 / 完了 1/13 タスク」と再実行の結果が同じ。
- 補足: `check_tasks.log` には実行したコマンド行（`$ python evals/check_tasks.py`）が書かれていない。T00 の評価で「証拠には実行したコマンドをそのまま記録する」と指摘済みなので、次からはコマンド行も残すこと。また `check_tasks.log` はまだコミットされていない（untracked）。

### 5. 記録コミットに秘密情報が入っていないか → ○
- `git show 54ef02b` の変更ファイルは `docs/requirements.md` と `evals/evidence/T01/requirements-diff.log` の2つだけ。`.env` は入っていない。
- `docs/safety.md` 3章のパターンで検索し、何も出なかった（下の再実行結果）。
- **指摘2**（不合格の理由ではない）: `evals/acceptance.md` では AC-00c の証拠は `secret-scan.log` だが、T01 の証拠に無い。今回は評価役が再実行して確認した。次のタスクからは実行役が `secret-scan.log` を残すこと。

## 自分で再実行したコマンドと結果

```
$ git rev-parse harness-baseline HEAD
54ef02b35d4c79b71f149e0834f4e71cb42ca995
54ef02b35d4c79b71f149e0834f4e71cb42ca995

$ git branch --show-current
feature/contest-jev-questions

$ git tag --points-at 54ef02b
harness-baseline

$ git show --stat 54ef02b
 docs/requirements.md                     | 12 +++++-----
 evals/evidence/T01/requirements-diff.log | 39 ++++++++++++++++++++++++++++++++
 2 files changed, 45 insertions(+), 6 deletions(-)

$ git show 54ef02b -- docs/requirements.md
（requirements-diff.log と同じ差分。index b807e02..df3820a、@@ -26 / @@ -49 / @@ -81 の3か所）

$ git diff 54ef02b HEAD -- docs/requirements.md | wc -l
0

$ git show 54ef02b | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
（出力なし、exit=1）

$ git diff HEAD | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
（出力なし、exit=1）

$ python evals/check_tasks.py   （tasks.json 更新前）
結果: エラー 0 件 / 警告 0 件 / 完了 1/13 タスク
```

## 差し戻し内容（実行役へ）
1. `docs/requirements.md` 3章の `[確定・Q2]` を、Q2 で答えてもらった「Questions」の項目だけに付け直す。「TypeSafe」の項目は `[仮定]` に戻すか、人間に確認して回答を記録する。
2. 直したあと、`requirements-diff.log`・`check_tasks.log`（コマンド行つき）・`secret-scan.log` を取り直し、人間に `harness-baseline` タグを付け直してもらう。
3. `docs/roles.md` 3章の完了条件どおり、不合格の理由を `progress.md` に書く（評価役は今回 review.md と tasks.json 以外の変更を禁止されているため、メインの AI が書くこと）。

## tasks.json 更新後の `python evals/check_tasks.py`

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 1/13 タスク
```
