# T01 再検品結果（評価役・2回目）

- 日付: 2026-09-26
- 対象: tasks.json T01「【人間】docs/requirements.md 5章の未確定事項 Q1〜Q3 に回答する」
- 1回目の記録: `evals/evidence/T01/review-1.md`（不合格。AC-02 ×）
- 対象コミット: `54ef02b`（回答の記録）→ `55d933e`（1回目の指摘の修正）→ `86bd2d7`（TypeSafe の確定と提案 P1 の反映）= `HEAD` = `harness-baseline`
- 人間の回答原文（メインの AI がプロンプトに転記したもの）
  - 1回目: 「Q1、良いです」「Q2、そうです」「Q3、僕のキーです」（Q3 は「Windows の環境変数 TYPESAFE_API_KEY が設定されていたが、あなたのキーか」という質問への返事）
  - 2回目: 「2あっています」（TypeSafe の解釈が合っているか）、「3採用してください」（提案 P1 を採用するか）
- 読んだ順: `docs/roles.md` 3章 → `evals/acceptance.md` → `tasks.json` の T01 → `evals/evidence/T01/` → `git show 55d933e 86bd2d7` / `git diff`
- 読んでいないもの: `backend/.env`、環境変数の値（指示どおり）

## 判定: **合格**（全て○）→ `status: "done"`, `passes: true`

| 条件 | 判定 | 根拠 |
|---|---|---|
| AC-02 未確定事項 Q1〜Q3 に人間の回答が記録されている（AI の推測ではない） | ○ | `docs/requirements.md` 5章の Q1〜Q3 が回答原文と一致。1回目の指摘（3章の見出しで TypeSafe まで確定扱い）は、項目ごとの印に直したうえで、TypeSafe は人間の2回目の回答「あっています」に基づいて確定になった。Q4〜Q6 は仮定のまま |
| AC-00c 秘密情報が含まれていない | ○ | `secret-scan.log` のコマンドを再実行して一致なし。T00 基準（`2472589`）から `HEAD` までの全差分でも、検索パターン自体を書いた行以外に一致なし。`.env` はコミットされていない |
| AC-00d `python evals/check_tasks.py` がエラー0件 | ○ | 再実行で「エラー 0 件 / 警告 0 件」。証拠 `check_tasks.log` と同じ（tasks.json 更新前は 完了 1/13） |

## 確認項目ごとの結果

### 1. 1回目の不合格理由が解消されているか → ○
- `55d933e` で3章の見出しから `[確定・Q2]` を外し、項目ごとに印を付けた。
  - 「Questions」の項目: `[確定・Q2]`（Q2「そうです」の範囲内）
  - 「TypeSafe」の項目: いったん `[仮定・人間に未確認]` に戻した（review-1.md の直し方の例どおり）
- `86bd2d7` で「TypeSafe」の項目を `[確定・2026-09-26 人間の回答「あっています」]` に変更。
  - 質問は「TypeSafe の解釈も合っていれば教えて」で、対象は3章の TypeSafe 項目（提供元 TypeSafe AI 社であること、型を決めてはじく設計方針とも一致させること）全体。回答「2あっています」でその項目を確定にするのは回答の範囲内と判断した。
  - 記録の引用は「あっています」で、原文の先頭の「2」（質問番号）は省かれているが、意味は変わらないので問題なし。
- 項目の本文は1回目から変わっていない（印だけ変更）。回答原文を超える内容は足されていない。

### 2. requirements.md の記録が回答原文の範囲内か → ○
- 1-2節: `[確定・Q1]`「このブランチを土台にする」→ Q1「良いです」の範囲内（1回目と同じ）
- 5章 Q1〜Q3: 1回目の検品から変わっておらず、回答原文と一致（review-1.md の確認項目1のとおり）
- 5章 Q4〜Q6: 「5固定」「0.5」「T11 の前に人間が用意」のまま、仮定の列にあり確定扱いになっていない → ○
- 5章の見出し「未確定事項（人間の回答待ち）」は Q4〜Q6 が残っているので間違いではない。

### 3. docs/roles.md の変更（P1）が人間の採用内容の範囲内か → ○
- 提案 P1（`progress.md` の提案欄）:「証拠の保存例」に「ログの1行目に `$ 実行したコマンド` を書く」を追加する。人間の回答「3採用してください」。
- `86bd2d7` の roles.md の差分は2章「証拠の保存例」の2行だけ:
  - 見出しに「（ログの1行目には、実行したコマンドをそのまま `$ ` 付きで書く）」を追加
  - 例のコマンドを `{ echo '$ ...'; ...; } | tee ...` に変更（1行目にコマンドを書く方法の具体例）
- 提案の内容をそのまま反映したもので、それ以外（評価役の章、合格条件など）は変わっていない → 範囲内。

### 4. `harness-baseline` タグが変更を含むコミットを指しているか → ○
- `git rev-parse harness-baseline HEAD` → どちらも `86bd2d7c59e9dfbb3d065910ed807fdbefe72f27`
- `86bd2d7` は requirements.md（TypeSafe の確定）と roles.md（P1）の変更を含む。
- `git diff harness-baseline -- docs/` → 差分なし（タグ以降 docs は変わっていない）
- 補足（不合格の理由ではない）: 作業ツリーに未コミットの変更がある（`evals/evidence/T01/check_tasks.log` にコマンド行を追加、`secret-scan.log` の対象に roles.md を追加、`tasks.json`）。証拠ファイルと tasks.json だけで、docs には無いのでタグの範囲の問題にはならない。メインの AI がこの review.md とあわせてコミットすること。

### 5. 証拠と再実行の結果が一致するか → ○
- `requirements-diff.log`: 1行目のコマンド `git diff 2472589 -- docs/requirements.md` を再実行し、2行目以降と `diff` で比較 → 完全に一致（index `b807e02..125b57d`）。
- `secret-scan.log`: 1行目のコマンドを再実行 → 出力なし（exit=1）。ログの「(一致なし)」と同じ。
- `check_tasks.log`: 再実行 → 「結果: エラー 0 件 / 警告 0 件 / 完了 1/13 タスク」。ログと同じ。
- 3つとも1行目に `$ 実行したコマンド` があり、P1 のルールと T00・T01 の過去の指摘に合っている。

### 6. 秘密情報が入っていないか → ○
- `git diff 2472589 HEAD` 全体を `docs/safety.md` 3章のパターンで検索すると5行出るが、全て検索コマンド自体を書いた行（証拠ログ・review の中のコマンド文字列）。`grep -vF 'grep -nE'` で除くと0件。
- 作業ツリーの差分（`git diff`）も同様に、コマンド文字列の行だけ。
- `2472589..HEAD` で変更されたファイルに `.env` は無い（追跡中なのは `backend/.env.example` と `frontend/.env.example` だけで、この期間に変更なし）。
- requirements.md の Q3 は環境変数の名前 `TYPESAFE_API_KEY` だけで、値は書かれていない。

## 自分で再実行したコマンドと結果

```
$ git log --oneline -8
86bd2d7 Confirm TypeSafe interpretation and adopt proposal P1
55d933e Fix T01 record: confirm only the Questions interpretation
54ef02b Record human answers to Q1-Q3 (T01)
f1f41cb Complete T00: work branch and harness baseline
2472589 Add AI harness for contest-question (Jev) feature
b2dfe7f Fall back to Claude-only scoring when TYPESAFE_API_KEY is unset
0447308 Remove ffmpeg dependency and prep for Vercel deployment
67b6a33 Use Jev (TypeSafe System One) for rubric scoring, Claude for commentary

$ git rev-parse harness-baseline HEAD
86bd2d7c59e9dfbb3d065910ed807fdbefe72f27
86bd2d7c59e9dfbb3d065910ed807fdbefe72f27

$ git tag --points-at HEAD
harness-baseline

$ git branch --show-current
feature/contest-jev-questions

$ git show --stat 55d933e 86bd2d7
（55d933e: docs/requirements.md, evals/evidence/T01/{check_tasks.log,requirements-diff.log,review-1.md,secret-scan.log}, progress.md, tasks.json）
（86bd2d7: docs/requirements.md | 2 +-, docs/roles.md | 4 ++--, evals/evidence/T01/requirements-diff.log | 4 ++--, progress.md | 7 ++++---）

$ git diff harness-baseline -- docs/
（出力なし）

$ git diff 2472589 -- docs/requirements.md > "$TEMP/rd.txt"; tail -n +2 evals/evidence/T01/requirements-diff.log | diff - "$TEMP/rd.txt" && echo SAME_REQDIFF
SAME_REQDIFF

$ git diff 2472589 -- docs/requirements.md docs/roles.md | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"; echo "exit=$?"
exit=1

$ git diff 2472589 HEAD | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"; echo "exit=$?"
178:+$ git show HEAD | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
179:+407:+- コミット前に確認: `git diff --cached | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"` で何も出ないこと。
348:+$ git show 54ef02b | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
351:+$ git diff HEAD | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
375:+$ git diff 2472589 -- docs/requirements.md | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
exit=0
（全て検索コマンドの文字列自体。次のコマンドで除外して確認）

$ git diff 2472589 HEAD | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+" | grep -vF 'grep -nE'; echo "exit=$?"
exit=1

$ git diff | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"; echo "exit=$?"
13:-$ git diff 2472589 -- docs/requirements.md | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
14:+$ git diff 2472589 -- docs/requirements.md docs/roles.md | grep -nE "sk-|ts-[A-Za-z0-9]{8,}|api_key\s*=\s*['\"][^'\"]+"
exit=0
（secret-scan.log の中のコマンド文字列だけ）

$ git log 2472589..HEAD --name-only --format= | sort -u | grep -E "(^|/)\.env$"; echo "envexit=$?"
envexit=1

$ git ls-files | grep -i "\.env"
backend/.env.example
frontend/.env.example

$ python evals/check_tasks.py   （tasks.json 更新前）
結果: エラー 0 件 / 警告 0 件 / 完了 1/13 タスク
```

## メインの AI への連絡
- T01 は合格。この review.md、tasks.json の更新、未コミットの証拠ファイル（`check_tasks.log`, `secret-scan.log`）をコミットすること。`evidence` に `evals/evidence/T01/review.md` を足すかどうかはメインの AI が判断する（評価役は status/passes 以外を変えていない）。
- `progress.md` の引き継ぎメモを「T01 合格」に更新すること。

## tasks.json 更新後の `python evals/check_tasks.py`

```
$ python evals/check_tasks.py
結果: エラー 0 件 / 警告 0 件 / 完了 2/13 タスク
```
